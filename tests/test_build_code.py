import unittest
from unittest.mock import patch, MagicMock, call
from argparse import Namespace
import sys
import os


sys.path.insert(0, f'{os.path.dirname(__file__)}/../scripts/')
from build import Builder, DEFAULT_REPO, IMAGE_ORDER  # noqa: E402


class TestBuilder(unittest.TestCase):

    def setUp(self):
        """Set up default arguments for each test."""
        self.default_args = Namespace(
            dryrun=False,
            debug=False,
            images=['fornax-main'],
            tag='test-tag',
            build=False,
            push=False,
            retag=None,
            ecr=None,
            extra_args=None,
            build_vars=None,
            export_locks=False,
            repo=None
        )

    def test_initialization(self):
        """Test if the builder initializes defaults correctly."""
        builder = Builder(self.default_args)
        self.assertEqual(builder.repo, DEFAULT_REPO)
        self.assertEqual(builder.tag, 'test-tag')
        self.assertFalse(builder.dryrun)

    @patch('build.subprocess.run')
    def test_run(self, mock_subprocess_run):
        """Test the run method."""
        builder = Builder(self.default_args)
        builder.run("docker --version", timeout=10)

        # Verify subprocess.run was called with the right arguments
        mock_subprocess_run.assert_called_once_with(
            "docker --version",
            shell=True,
            check=True,
            text=True,
            timeout=10
        )

    def test_check_input_missing_images(self):
        """Test validation fails when build is requested but no
        images are provided."""

        self.default_args.images = None

        # build
        self.default_args.build = True
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue("No images passed" in str(context.exception))
        self.default_args.build = False

        # push
        self.default_args.push = True
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue("No images passed" in str(context.exception))
        self.default_args.push = False

        # export-locks
        self.default_args.export_locks = True
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue("No images passed" in str(context.exception))
        self.default_args.export_locks = None

    @patch('build.Builder.run')
    def test_check_input_gets_git_branch(self, mock_run):
        """Test that missing tag attempts to fetch from git."""
        self.default_args.build = True
        self.default_args.tag = None
        builder = Builder(self.default_args)

        # Mock the stdout of the git command
        mock_result = MagicMock()
        mock_result.stdout = "main-branch\n"
        mock_run.return_value = mock_result

        builder.check_input()

        # Assert git branch was checked and tag was updated
        mock_run.assert_called_once_with(
            'git branch --show-current', 100, capture_output=True)
        self.assertEqual(builder.tag, 'main-branch')

    def test_check_input_retag(self):
        """Test retag in check_input."""
        self.default_args.retag = ''
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue("--retag expects a list" in str(context.exception))

    def test_check_input_ecr(self):
        """Test ecr in check_input."""
        # not a list
        self.default_args.ecr = ''
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue("--ecr expects a list" in str(context.exception))

        # not url
        self.default_args.ecr = ['not-url']
        builder = Builder(self.default_args)
        with self.assertRaises(ValueError) as context:
            builder.check_input()
        self.assertTrue(
            "--ecr expects url endpoints" in str(context.exception))

    def test_check_input_build_vars(self):
        """Test --build-vars in check_input."""
        self.default_args.build_vars = ''
        builder = Builder(self.default_args)
        builder.check_input()
        self.assertEqual(builder.build_vars, [])

        # check wrong format
        wrong_format = ['var1', 'var1 = 23 var2=1']
        for wrong in wrong_format:
            self.default_args.build_vars = wrong
            builder = Builder(self.default_args)
            with self.assertRaises(ValueError) as context:
                builder.check_input()
            self.assertTrue(
                "--build-var expects" in str(context.exception))

    def test_get_full_tag(self):
        """Test getting full tag."""
        builder = Builder(self.default_args)
        full_tag = builder.get_full_tag('fornax-main', 'dev')
        self.assertEqual(full_tag, f"{DEFAULT_REPO}/fornax-main:dev")

        # Test failure on invalid tag format
        with self.assertRaises(ValueError):
            builder.get_full_tag('fornax-main', 'invalid:tag')

    @patch('build.Builder.run')
    def test_do_export_locks(self, mock_run):
        """Test docker build command generation."""
        self.default_args.export_locks = True
        self.default_args.images = ['fornax-1', 'fornax-2']

        builder = Builder(self.default_args)

        builder.do_export_locks()

        # call run twice, create a folder and export
        self.assertEqual(mock_run.call_count, 4)

        def full_tag(image):
            return f'{DEFAULT_REPO}/{image}:{self.default_args.tag}'

        def lock_dir(image):
            return f'{image}_locks'

        expected_calls = [
            call(f"mkdir -p {lock_dir('fornax-1')}", 100),
            call(f"docker run --entrypoint=\"\" --rm -v $PWD/{lock_dir('fornax-1')}:/host --user `id -u` {full_tag('fornax-1')} bash -c 'cp -r $LOCK_DIR/* /host/'", 1000),  # noqa E501
            call(f"mkdir -p {lock_dir('fornax-2')}", 100),
            call(f"docker run --entrypoint=\"\" --rm -v $PWD/{lock_dir('fornax-2')}:/host --user `id -u` {full_tag('fornax-2')} bash -c 'cp -r $LOCK_DIR/* /host/'", 1000),  # noqa E501
        ]
        mock_run.assert_has_calls(expected_calls, any_order=False)

    @patch('build.Builder.run')
    @patch('build.Builder.copy_common_files')
    @patch('build.Builder.extract_kernel_files')
    def test_do_build(self, mock_extract, mock_copy, mock_run):
        """Test docker build command generation."""
        self.default_args.build = True
        self.default_args.images = ['fornax-slim']
        self.default_args.build_vars = ['TEST_VAR=123']
        self.default_args.extra_args = ['--network=host']

        builder = Builder(self.default_args)
        time_tag = "20260512_1200"

        builder.do_build(time_tag)

        # Verify common files were copied and kernels were extracted
        mock_copy.assert_called_with('fornax-slim')
        mock_extract.assert_called_once()

        # Verify the generated docker build command
        # You can inspect the arguments passed to 'run'
        called_args = mock_run.call_args_list[0][0][0]
        self.assertIn("docker build", called_args)
        self.assertIn("--platform=linux/amd64", called_args)
        self.assertIn("--build-arg TEST_VAR=123", called_args)
        self.assertIn("--network=host", called_args)
        self.assertIn(
            f"--tag {DEFAULT_REPO}/fornax-slim:test-tag", called_args)
        self.assertIn(
            f"--tag {DEFAULT_REPO}/fornax-slim:{time_tag}", called_args)

    @patch('build.Builder.run')
    def test_do_push(self, mock_run):
        """Test docker push command generation."""
        self.default_args.push = True
        self.default_args.images = ['fornax-main']

        builder = Builder(self.default_args)

        builder.do_push()
        mock_run.assert_called_once()

        # Verify the generated docker build command
        # You can inspect the arguments passed to 'run'
        called_args = mock_run.call_args_list[0][0][0]
        self.assertIn("docker push", called_args)
        self.assertIn(
            f"{DEFAULT_REPO}/{self.default_args.images[0]}:test-tag",
            called_args
        )

    @patch('build.Builder.run')
    def test_do_retag(self, mock_run):
        """Test docker retag command generation."""
        self.default_args.retag = ['main', 'stable']
        self.default_args.images = ['fornax-main']

        builder = Builder(self.default_args)

        builder.do_retag()
        # we expect 5 calls: 1 pull, and 1-tag, 1-push for each tag.
        self.assertEqual(mock_run.call_count, 5)

        expected_calls = [
            call('docker pull ghcr.io/nasa-fornax/fornax-images/fornax-main:test-tag', timeout=3000),  # noqa E501
            call('docker tag ghcr.io/nasa-fornax/fornax-images/fornax-main:test-tag ghcr.io/nasa-fornax/fornax-images/fornax-main:main', timeout=1000),  # noqa E501
            call('docker push ghcr.io/nasa-fornax/fornax-images/fornax-main:main', timeout=3000),  # noqa E501
            call('docker tag ghcr.io/nasa-fornax/fornax-images/fornax-main:test-tag ghcr.io/nasa-fornax/fornax-images/fornax-main:stable', timeout=1000),  # noqa E501
            call('docker push ghcr.io/nasa-fornax/fornax-images/fornax-main:stable', timeout=3000)  # noqa E501
        ]
        mock_run.assert_has_calls(expected_calls, any_order=False)

    @patch('build.Builder.run')
    def test_do_retag_no_image(self, mock_run):
        """Test docker retag command when no image is passed."""
        self.default_args.retag = ['main']
        self.default_args.images = None

        builder = Builder(self.default_args)

        builder.do_retag()
        # we expect 12 calls: (1 pull, and 1-tag, 1-push) for each image
        self.assertEqual(mock_run.call_count, 12)

        expected_calls = []
        for im in [_im for _im in IMAGE_ORDER if _im.startswith('fornax-')]:
            expected_calls += [
                call(f'docker pull ghcr.io/nasa-fornax/fornax-images/{im}:test-tag', timeout=3000),  # noqa E501
                call(f'docker tag ghcr.io/nasa-fornax/fornax-images/{im}:test-tag ghcr.io/nasa-fornax/fornax-images/{im}:main', timeout=1000),  # noqa E501
                call(f'docker push ghcr.io/nasa-fornax/fornax-images/{im}:main', timeout=3000),  # noqa E501
            ]
        mock_run.assert_has_calls(expected_calls, any_order=False)

    @patch('build.urllib.request.urlopen')
    def test_do_ecr(self, mock_urlopen):
        """Test triggering ECR endpoint."""
        self.default_args.ecr = ['https://fake.endpoint.com']
        self.default_args.images = ['fornax-slim']
        builder = Builder(self.default_args)

        # Setup mock response
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"Success"
        mock_urlopen.return_value = mock_resp

        builder.do_ecr()

        # Verify urlopen was called
        mock_urlopen.assert_called_once()
        called_request = mock_urlopen.call_args[0][0]
        self.assertEqual(
            called_request.full_url,
            f"{self.default_args.ecr[0]}?image=fornax-slim&tag=test-tag"
        )
