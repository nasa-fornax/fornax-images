import unittest
from unittest.mock import patch
import logging
import sys
import os
import pathlib
import tempfile
import glob
from io import StringIO


sys.path.insert(0, f'{os.path.dirname(__file__)}/../scripts/')
from builder import TaskRunner, Builder  # noqa: E402
from changed_images import find_changed_images  # noqa: E402


class TestTaskRunner(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        self.builder_run = TaskRunner(logger, dryrun=False)
        self.builder_dry = TaskRunner(logger, dryrun=True)
        self.logger = logger

    def test_run(self):
        out = self.builder_run.run('pwd', timeout=100, capture_output=True)
        self.assertEqual(out.stdout.strip().lower(), os.getcwd().lower())

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


class TestBuilder(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        self.repo = 'some-repo'
        self.registry = 'my-registry'
        self.tag = 'some-tag'
        self.image = 'some-image'

        self.builder_run = Builder(
            self.repo, logger, registry=self.registry, dryrun=False
        )
        self.builder_dry = Builder(
            self.repo, logger, registry=self.registry, dryrun=True
        )
        self.logger = logger

    def test_get_full_tag(self):
        full_tag = self.builder_dry.get_full_tag(self.image, self.tag)
        self.assertEqual(
            full_tag, f'{self.registry}/{self.repo}/{self.image}:{self.tag}'
        )

    def test_check_tag(self):
        with self.assertRaises(ValueError):
            self.builder_dry.check_tag('repo:tag')
        with self.assertRaises(ValueError):
            self.builder_dry.check_tag(['repo'])
        self.builder_dry.check_tag('tag')
        self.logger.handlers.clear()

    def test_build__basic(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.image, self.tag)
            output = mock_out.getvalue().strip()
        full_tag = self.builder_dry.get_full_tag(self.image, self.tag)
        cmd = (f'docker build --build-arg REPOSITORY={self.repo} '
               f'--build-arg REGISTRY={self.registry} '
               f'--build-arg BASE_TAG={self.tag} '
               f'--tag {full_tag} {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()

    def test_build__build_args_is_list(self):
        with self.assertRaises(ValueError):
            self.builder_dry.build(self.image, self.tag, build_args='ENV=val')
        self.logger.handlers.clear()

    def test_build__build_args(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.image, self.tag,
                                   build_args=['ENV=val', 'ENV2=val'])
            output = mock_out.getvalue().strip()
        full_tag = self.builder_dry.get_full_tag(self.image, self.tag)
        cmd = (f'docker build --build-arg ENV=val --build-arg ENV2=val '
               f'--build-arg REPOSITORY={self.repo} '
               f'--build-arg REGISTRY={self.registry} '
               f'--build-arg BASE_TAG={self.tag} '
               f'--tag {full_tag} {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()

    def test_build__extra_args(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.build(self.image, self.tag,
                                   extra_args='--some-par')
            output = mock_out.getvalue().strip()
        full_tag = self.builder_dry.get_full_tag(self.image, self.tag)
        cmd = (f'docker build --build-arg REPOSITORY={self.repo} '
               f'--build-arg REGISTRY={self.registry} '
               f'--build-arg BASE_TAG={self.tag} --some-par '
               f'--tag {full_tag} {self.image}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()

    def test_build__push_not_str(self):
        with self.assertRaises(ValueError):
            self.builder_dry.push(self.image, 123)
        self.logger.handlers.clear()

    def test_build__push_wrong_format(self):
        with self.assertRaises(ValueError):
            self.builder_dry.push(self.image, f'{self.image}:{self.tag}')
        self.logger.handlers.clear()

    def test_build__push(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.push(self.image, self.tag)
            output = mock_out.getvalue().strip()
        cmd = (f'docker push {self.registry}/{self.repo}/'
               f'{self.image}:{self.tag}')
        self.assertEqual(cmd, output.split('::')[-1].strip())
        self.logger.handlers.clear()

    def test_build__release__tag_not_list(self):
        with self.assertRaises(ValueError):
            self.builder_dry.release('tag', 'out')
        # the following should work
        self.builder_dry.release('tag', ['out'])

    def test_build__release__wrong_tag(self):
        # wrong release tag
        with self.assertRaises(ValueError):
            self.builder_dry.release('tag', ['tag:out'])

        # wrong source tag
        with self.assertRaises(ValueError):
            self.builder_dry.release('tag:in', ['tag'])

    def test_build__release__images_not_list(self):
        with self.assertRaises(ValueError):
            self.builder_dry.release('tag', ['out'], images='images')

    def test_build__release__images_unknown_image(self):
        with self.assertRaises(ValueError):
            self.builder_dry.release('tag', ['out'], images=['some_image'])
        # the following should work
        self.builder_dry.release('tag', ['out'], ['base-image'])

    def test_build__release(self):
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            self.builder_dry.release(
                f'{self.tag}', [f'{self.tag}-out'], images=['base-image'])
            output = mock_out.getvalue().strip()
        source_tag = self.builder_dry.get_full_tag('base-image', self.tag)
        release_tag = self.builder_dry.get_full_tag('base-image',
                                                    f'{self.tag}-out')
        self.assertTrue(f'docker pull {source_tag}' in output)
        self.assertTrue(f'docker tag {source_tag} {release_tag}' in output)
        self.assertTrue(f'docker push {release_tag}' in output)
        self.logger.handlers.clear()

    def test_remove_lockfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = ["conda-lock.yml", "conda-notebook-lock.yml",
                     "conda-a.yml"]
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
            self.builder_dry.update_lockfiles(tmpdir, self.tag)
            self.builder_dry.run = _run
            with open(os.path.join(tmpdir, "conda-a-lock.yml"), "r") as f:
                result = f.read()
            nowfiles = os.listdir(tmpdir)
            self.assertEqual(len(nowfiles), 3)
            self.assertEqual(result, "name:\nnextline")
        self.logger.handlers.clear()


class TestChangedImages(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        self.runner = TaskRunner(logger, dryrun=True)
        self.logger = logger

    def test_pull_request(self):
        pull_request_event = {
            'event_name': 'pull_request',
            'event': {
                'base_ref': '7905b4edab6'
            }
        }
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            res = find_changed_images(pull_request_event, self.runner)
            output = mock_out.getvalue().strip()
        base_ref = pull_request_event['event']['base_ref']
        self.assertTrue(f'git fetch origin {base_ref}' in output)
        self.assertTrue(
            f'git --no-pager diff --name-only HEAD origin/${base_ref} '
            f'| xargs -n1 dirname | sort -u' in output
        )
        self.assertEqual(res, [])
        self.logger.handlers.clear()

    def test_push(self):
        push_event = {
            'event_name': 'push',
            'event': {
                'before': '299390bb5c8',
                'after': '2add5c8e038'
            }
        }
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            res = find_changed_images(push_event, self.runner)
            output = mock_out.getvalue().strip()
        before = push_event['event']['before']
        after = push_event['event']['after']
        self.assertTrue(f'git fetch origin {before}' in output)
        self.assertTrue((
            f'git --no-pager diff-tree --name-only -r {before}..{after}'
            ' | xargs -n1 dirname | sort -u') in output
        )
        self.assertEqual(res, [])
        self.logger.handlers.clear()

    def test_push_new(self):
        push_event = {
            'event_name': 'push',
            'event': {
                'before': '00000000000',
                'after': '2add5c8e038'
            }
        }
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            res = find_changed_images(push_event, self.runner)
            output = mock_out.getvalue().strip()
        self.assertTrue(
            ("find . -type f -name 'Dockerfile' -exec dirname {} \\; "
             "| sed 's|^\\./||'") in output)
        self.assertEqual(res, [])
        self.logger.handlers.clear()

    def test_else_event(self):
        else_event = {'event_name': 'other'}
        with patch('sys.stderr', new=StringIO()) as mock_out:
            logging.basicConfig(level=logging.DEBUG)
            res = find_changed_images(else_event, self.runner)
            output = mock_out.getvalue().strip()
        self.assertTrue(
            'git ls-files | xargs -n1 dirname | sort -u' in output
        )
        self.assertEqual(res, [])
        self.logger.handlers.clear()


if __name__ == "__main__":
    unittest.main()
