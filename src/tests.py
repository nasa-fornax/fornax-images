import glob
import logging
import os
import pathlib
import subprocess
import tempfile
import unittest

import buildimages
import neededimages
import release

# python3.11 -m unittest discover -s src or python src/test.py


class DummyBuilder:
    def __init__(self):
        self.logged = []
        self.builds = []
        self.removed_lockfiles = []
        self.updated_lockfiles = []
        self.chdirs = []
        self.pushed = []

    def builds_necessary(self, repository_name, release_tag, images):
        return [("a", "tag")]

    def out(self, msg, severity=None):
        self.logged.append(msg)

    def build(
        self, repository, dockerdir, tags, no_cache, build_args, plain=False
    ):
        self.builds.append((repository, dockerdir, tags, no_cache, build_args))

    def remove_lockfiles(self, dockerdir):
        self.removed_lockfiles.append(dockerdir)

    def update_lockfiles(self, dockerdir, repository_name, tag):
        self.updated_lockfiles.append((dockerdir, repository_name, tag))

    def push(self, tags):
        self.pushed.append(tags)

    def chdir(self, path):
        self.chdirs.append(path)


class TestMain(unittest.TestCase):
    def test_conflicting_params(self):
        builder = DummyBuilder()
        with self.assertRaises(SystemExit):
            buildimages.main(
                builder,
                "repo_name",
                "release_tag",
                no_build=True,
                do_push=True,
            )
        self.assertEqual(
            builder.logged, ["--no-build and --do-push cannot be used together"]
        )

    def test_main_nobuild(self):
        builder = DummyBuilder()
        buildimages.main(
            builder,
            "repo_name",
            "release_tag",
            no_build=True,
        )
        self.assertEqual(
            builder.logged, ["Repository repo_name, tag release_tag"]
        )
        self.assertEqual(builder.removed_lockfiles, [])
        self.assertEqual(builder.builds, [])
        self.assertEqual(builder.updated_lockfiles, [])
        self.assertEqual(
            builder.chdirs, [os.path.dirname(os.path.dirname(__file__))]
        )
        self.assertEqual(builder.pushed, [])

    def test_main_update_lock(self):
        builder = DummyBuilder()
        buildimages.main(
            builder,
            "repo_name",
            "release_tag",
            update_lock=True,
        )
        self.assertEqual(
            builder.logged, ["Repository repo_name, tag release_tag"]
        )
        self.assertEqual(builder.removed_lockfiles, ["a"])
        self.assertEqual(
            builder.builds, [("repo_name", "a", "tag", False, None)]
        )
        self.assertEqual(builder.updated_lockfiles, [("a", "repo_name", "tag")])
        self.assertEqual(builder.pushed, [])

    def test_main_do_push(self):
        builder = DummyBuilder()
        buildimages.main(
            builder,
            "repo_name",
            "release_tag",
            do_push=True,
        )
        self.assertEqual(
            builder.logged, ["Repository repo_name, tag release_tag"]
        )
        self.assertEqual(builder.removed_lockfiles, [])
        self.assertEqual(
            builder.builds, [("repo_name", "a", "tag", False, None)]
        )
        self.assertEqual(builder.updated_lockfiles, [])
        self.assertEqual(builder.pushed, ["tag"])


class DummyLogger:
    def __init__(self):
        self.messages = []

    def log(self, severity, msg):
        self.messages.append((severity, msg))


class TestBuilder(unittest.TestCase):
    def _makeOne(self):
        logger = DummyLogger()
        return buildimages.Builder(logger)

    def test_out(self):
        builder = self._makeOne()
        builder.out("foo", logging.ERROR)
        self.assertEqual(builder.logger.messages, [(logging.ERROR, "foo")])

    def test_run_success(self):
        builder = self._makeOne()
        result = builder.run("true", 200)
        self.assertEqual(
            builder.logger.messages,
            [(logging.INFO, "Running true with timeout 200")],
        )
        self.assertEqual(result.returncode, 0)

    def test_run_fail(self):
        builder = self._makeOne()
        with self.assertRaises(subprocess.CalledProcessError):
            builder.run("/wont/exist", 200, capture_output=True)
        self.assertEqual(
            builder.logger.messages,
            [(logging.INFO, "Running /wont/exist with timeout 200")],
        )

    def test_push(self):
        builder = self._makeOne()
        ran = []

        def run(command, timeout):
            ran.append((command, timeout))

        builder.run = run
        builder.push("a")
        self.assertEqual(ran, [("docker push a", 1000)])

    def test_remove_lockfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = ["conda-lock.yml", "conda-notebook-lock.yml", "conda-a.yml"]
            for fn in files:
                fn = os.path.join(tmpdir, fn)
                pathlib.Path(fn).touch()
            builder = self._makeOne()
            builder.remove_lockfiles(tmpdir)
            self.assertEqual(len(builder.logger.messages), 3)
            self.assertTrue(
                builder.logger.messages[0][1].startswith("Removing the lock")
            )
            self.assertEqual(glob.glob(f"{tmpdir}/conda-*lock.yml"), [])
            self.assertEqual(
                glob.glob(f"{tmpdir}/conda-*"),
                [os.path.join(tmpdir, "conda-a.yml")],
            )

    def test_chdir(self):
        builder = self._makeOne()
        oldwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                builder.chdir(tmpdir)
                self.assertEqual(os.getcwd(), tmpdir)
        finally:
            os.chdir(oldwd)

    def test_builds_necessary_unknown_image(self):
        builder = self._makeOne()
        with self.assertRaises(SystemExit):
            builder.builds_necessary("repo", "tag", ["nerp"])
        self.assertEqual(
            builder.logger.messages,
            [(logging.ERROR, "Unknown image name nerp")],
        )

    def test_builds_necessary(self):
        builder = self._makeOne()
        res = builder.builds_necessary("repo", "tag", ["tractor", "base_image"])
        self.assertEqual(
            res,
            [
                (
                    "base_image",
                    "ghcr.io/repo/base_image:tag",
                ),
                (
                    "tractor",
                    "ghcr.io/repo/tractor:tag",
                ),
            ],
        )

    def test_build_bad_build_arg(self):
        builder = self._makeOne()
        with self.assertRaises(ValueError):
            builder.build("repo_name", "path", "a:main", build_args=["a"])

    def test_build_bad_build_arg2(self):
        builder = self._makeOne()
        with self.assertRaises(ValueError):
            builder.build("repo_name", "path", "a:main", build_args=["a==0"])

    def test_build(self):
        builder = self._makeOne()
        ran = []

        def run(command, timeout):
            ran.append((command, timeout))

        builder.run = run
        builder.build(
            "repo_name", "path", "a:main", no_cache=True, build_args=["n=1"]
        )
        self.assertEqual(
            ran,
            [
                (
                    "docker build "
                    "--build-arg n=1 "
                    "--build-arg REPOSITORY=repo_name "
                    "--build-arg BASE_IMAGE_TAG=main "
                    "--build-arg IMAGE_TAG=main "
                    "--no-cache=true "
                    "--tag a:main path",
                    10000,
                ),
            ],
        )

    def test_build_custom_repo_name(self):
        builder = self._makeOne()
        ran = []

        def run(command, timeout):
            ran.append((command, timeout))

        builder.run = run
        builder.build(
            "repo_name",
            "path",
            "a:main",
            no_cache=True,
            build_args=["n=1", "REPOSITORY=another"],
        )
        self.assertEqual(
            ran,
            [
                (
                    "docker build --build-arg n=1 "
                    "--build-arg REPOSITORY=another "
                    "--build-arg BASE_IMAGE_TAG=main "
                    "--build-arg IMAGE_TAG=main "
                    "--no-cache=true "
                    "--tag a:main path",
                    10000,
                ),
            ],
        )

    def test_update_lockfiles(self):
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
            builder = self._makeOne()
            builder.run = run
            builder.update_lockfiles(tmpdir, "repo_name", "tag")
            with open(os.path.join(tmpdir, "conda-a-lock.yml"), "r") as f:
                result = f.read()
            self.assertEqual(len(builder.logger.messages), 1)
            nowfiles = os.listdir(tmpdir)
            self.assertEqual(len(nowfiles), 3)
            self.assertEqual(result, "name:\nnextline")


class TestTagger(unittest.TestCase):
    def test_tag(self):
        logger = DummyLogger()
        ran = []

        def run(command, timeout):
            ran.append((command, timeout))

        tagger = release.Tagger(logger)

        tagger.run = run
        tagger.tag("repo", "release", "source_tag")
        self.assertEqual(
            ran,
            [
                ("docker pull ghcr.io/repo/base_image:source_tag", 1000),
                (
                    "docker tag ghcr.io/repo/base_image:source_tag ghcr.io/repo/base_image:release",
                    500,
                ),
                ("docker push ghcr.io/repo/base_image:release", 1000),
                ("docker pull ghcr.io/repo/tractor:source_tag", 1000),
                (
                    "docker tag ghcr.io/repo/tractor:source_tag ghcr.io/repo/tractor:release",
                    500,
                ),
                ("docker push ghcr.io/repo/tractor:release", 1000),
            ],
        )


class TestNeeder(unittest.TestCase):
    def test_needs_all_due_to_no_tags(self):
        logger = DummyLogger()
        ran = []

        class DummyProcessResult:
            stdout = '{"tags": []}'

        def run(command, timeout, capture_output=True):
            ran.append((command, timeout))
            return DummyProcessResult

        needer = neededimages.Needer(logger)

        needer.run = run
        result = needer.needs("repo", "token", "[]", "main")
        self.assertEqual(result, ["base_image", "tractor"])

    def test_needs_one_due_to_no_tag(self):
        logger = DummyLogger()
        ran = []

        class DummyProcessResult:
            stdout = '{"tags": ["main"]}'

        class TractorDummyProcessResult:
            stdout = '{"tags": []}'

        def run(command, timeout, capture_output=True):
            ran.append((command, timeout))
            if len(ran) <= 1:
                return DummyProcessResult
            return TractorDummyProcessResult

        needer = neededimages.Needer(logger)

        needer.run = run
        result = needer.needs("repo", "token", "[]", "main")
        self.assertEqual(result, ["tractor"])

    def test_needs_one_due_to_dirchange(self):
        logger = DummyLogger()
        ran = []

        class DummyProcessResult:
            stdout = '{"tags": ["main"]}'

        def run(command, timeout, capture_output=True):
            ran.append((command, timeout))
            return DummyProcessResult

        needer = neededimages.Needer(logger)

        needer.run = run
        result = needer.needs("repo", "token", '["tractor"]', "main")
        self.assertEqual(result, ["tractor"])


if __name__ == "__main__":
    unittest.main()
