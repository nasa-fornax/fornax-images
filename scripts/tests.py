import unittest
from unittest.mock import patch
import logging
import sys
import os
import pathlib
import tempfile
import glob
from io import StringIO


sys.path.insert(0, os.getcwd())
from build import Builder


class TestBuilder(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        self.builder_run = Builder(logger, dryrun=False)
        self.builder_dry = Builder(logger, dryrun=True)
        self.logger = logger

        self.repo = 'some-repo'
        self.tag = 'some-tag'
        self.image = 'some-image'
    
    def test_run(self):
        out = self.builder_run.run('pwd', timeout=100, capture_output=True)
        self.assertEqual(out.stdout.strip(), os.getcwd().lower())


    def test_out(self):
        msg = 'test logging ...'
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_run.out(msg)
            output = mock_out.getvalue().strip()
        self.assertEqual(msg, output.split(':')[-1].strip())
        self.logger.handlers.clear()

    
    def test_dryrun(self):
        out = self.builder_dry.run('ls', timeout=100, capture_output=True)
        self.assertEqual(out, None)

        out = self.builder_run.run('ls', timeout=100, capture_output=True)
        self.assertNotEqual(out, None)

    def test_build__basic(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.repo, self.image, self.tag)
            output = mock_out.getvalue().strip()
        cmd = (f'docker build --build-arg REPOSITORY={self.repo} '
               f'--build-arg IMAGE_TAG={self.tag} --tag some-tag {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()
    
    def test_build__build_args_is_list(self):
        with self.assertRaises(ValueError):
            self.builder_dry.build(self.repo, self.image, self.tag, build_args='ENV=val')
        self.logger.handlers.clear()
    
    def test_build__build_args(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.repo, self.image, self.tag,
                                    build_args=['ENV=val', 'ENV2=val'])
            output = mock_out.getvalue().strip()
        cmd = (f'docker build --build-arg ENV=val --build-arg ENV2=val '
               f'--build-arg REPOSITORY={self.repo} '
               f'--build-arg IMAGE_TAG={self.tag} --tag some-tag {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()
    
    def test_build__extra_args(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.repo, self.image, self.tag,
                                    extra_args='--some-par')
            output = mock_out.getvalue().strip()
        cmd = (f'docker build --build-arg REPOSITORY={self.repo} --build-arg '
               f'IMAGE_TAG={self.tag} --some-par --tag some-tag {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()

    def test_build__push_not_str(self):
        with self.assertRaises(ValueError):
            self.builder_dry.push(123)
        self.logger.handlers.clear()
    
    def test_build__push_wrong_format(self):
        with self.assertRaises(ValueError):
            self.builder_dry.push(self.tag)
        self.logger.handlers.clear()
    
    def test_build__push(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.push(f'{self.repo}:{self.tag}')
            output = mock_out.getvalue().strip()
        cmd = (f'docker push {self.repo}:{self.tag}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()
    
    def test_build__release__tag_not_list(self):
        with self.assertRaises(ValueError):
            self.builder_dry.release('repo', 'in:tag', 'out')

    def test_build__release_wrong_tag(self):
        with self.assertRaises(ValueError):
            self.builder_dry.release('repo', 'in:tag', ['out'])
        with self.assertRaises(ValueError):
            self.builder_dry.release('repo', 'in', ['out:tag'])
        self.logger.handlers.clear()
    
    def test_build__release(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.release(f'{self.repo}', f'{self.tag}', [f'{self.tag}-out'])
            output = mock_out.getvalue().strip()
        cmd = (f'docker push {self.repo}:{self.tag}')
        self.assertTrue(f'docker pull ghcr.io/{self.repo}/base_image:{self.tag}' in output)
        self.assertTrue((f'docker tag ghcr.io/{self.repo}/base_image:{self.tag} '
                         f'ghcr.io/{self.repo}/base_image:{self.tag}-out') in output)
        self.assertTrue(f'docker push ghcr.io/{self.repo}/base_image:{self.tag}-out' in output)
        self.logger.handlers.clear()

    def test_remove_lockfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = ["conda-lock.yml", "conda-notebook-lock.yml", "conda-a.yml"]
            for fn in files:
                fn = os.path.join(tmpdir, fn)
                pathlib.Path(fn).touch()
            self.builder_run.remove_lockfiles(tmpdir)
            self.assertEqual(glob.glob(f'{tmpdir}/conda-*lock.yml'), [])
            self.assertEqual(
                glob.glob(f"{tmpdir}/conda-*"),
                [os.path.join(tmpdir, "conda-a.yml")],
            )
    
    def test_update_lockfiles(self):
        # dummy builder to write to stdout
        class DummyResult:
            stdout = "woo\nyoo\nname:\nnextline"
        ran = []
        def run(cmd, timeout, **kw):
            ran.append((cmd, timeout))
            return DummyResult
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = [
                "conda-notebook-lock.yml",
                "conda-a.yml",
                "conda-a-lock.yml",
            ]
            for fn in files:
                fn = os.path.join(tmpdir, fn)
                pathlib.Path(fn).touch()
            _run = self.builder_dry.run
            self.builder_dry.run = run
            self.builder_dry.update_lockfiles(tmpdir, 'main:tag')
            self.builder_dry.run = _run
            with open(os.path.join(tmpdir, "conda-a-lock.yml"), "r") as f:
                result = f.read()
            nowfiles = os.listdir(tmpdir)
            self.assertEqual(len(nowfiles), 3)
            self.assertEqual(result, "name:\nnextline")
        self.logger.handlers.clear()

if __name__ == "__main__":
    unittest.main()