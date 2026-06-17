import logging
import sys
import os
import shutil
import urllib.request
import urllib.error
import time
import argparse
import subprocess
from datetime import datetime


DEFAULT_REPO = "ghcr.io/nasa-fornax/fornax-images"
IMAGE_ORDER = (
    'jupyter-base',
    'fornax-base',
    'env-core',
    'fornax-nb',
    'archive-nb',
    'env-heasoft',
    'env-ciao',
    'env-fermi',
    'env-sas',
    'fornax-main',
    'fornax-hea',
    'fornax-slim'
)
# images that contains environments
SOFTWARE_IMAGES = [
    im for im in IMAGE_ORDER if im.startswith('env-') or '-nb' in im
]
COMMON_FILES = ['introduction.md', 'changes.md']


class Builder:
    """For holding common build parameters"""

    def __init__(self, args):
        """Initialize the builder"""

        # process input
        self.dryrun = args.dryrun
        self.debug = args.debug

        self.images = args.images

        self.tag = args.tag

        self.build = args.build
        self.push = args.push
        self.retag = args.retag
        self.ecr = args.ecr

        self.extra_args = args.extra_args

        self.build_vars = args.build_vars

        self.export_locks = args.export_locks

        self.repo = args.repo
        if self.repo is None:
            self.repo = DEFAULT_REPO

        # Setup logger
        self.setup_logger()

    def print(self, msg, severity=logging.DEBUG):
        """Print helper"""
        self.logger.log(severity, msg)
        sys.stdout.flush()

    def run(self, command, timeout, **runargs):
        """Run system command {command} with a timeout

        Args:
        -----
        command: str
            Command to pass to subprocess.run()
        timeout: int
            Timeout in sec
        **runargs:
            to be passed to subprocess.run
        """
        self.print(command, logging.INFO)
        result = None
        if not self.dryrun:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                timeout=timeout,
                **runargs,
            )
        return result

    def setup_logger(self):
        """Setup the looger"""

        logging.basicConfig(
            format="%(asctime)s|%(levelname)5s| %(message)s",
            datefmt="%Y-%m-%d|%H:%M:%S",
        )

        self.logger = logging.getLogger('::Fornax-Build::')
        level = logging.DEBUG if self.debug else logging.INFO
        self.logger.setLevel(level=level)

    def input_summary(self):
        """Summarize the input"""

        self.print("="*30)
        self.print(" :: Fornax image builder ::")
        self.print("-"*30)
        info = {
            'images': self.images,
            'tag': self.tag,
            'repo': self.repo,
            'build?': self.build,
            'push?': self.push,
            'ecr': self.ecr if self.ecr is None else len(self.ecr),
            'retag': self.retag,
            'extra-args': self.extra_args,
            'build-args': self.build_vars,
            'debug?': self.debug,
            'dry-run?': self.dryrun,

        }
        for key, val in info.items():
            self.print(f"{key:>12}: {val}")
        self.print("="*30)

    def check_input(self):
        """Check all the required input is passed"""
        need_image = False
        need_tag = False

        if (
            self.export_locks or
            self.build or
            self.push
        ):
            need_image = True

        if need_image or self.ecr is not None or self.retag:
            need_tag = True

        if need_image and self.images is None:
            raise ValueError("No images passed")

        if need_tag and self.tag is None:
            # get defaut tag from branch name
            out = self.run(
                'git branch --show-current', 100, capture_output=True)
            if out is not None:
                self.tag = out.stdout.strip()
            else:
                raise ValueError("--tag is required")

        if self.retag is not None:
            if not isinstance(self.retag, list):
                raise ValueError(f'--retag expects a list: {self.retag}')

        if self.ecr is not None:
            if not isinstance(self.ecr, list):
                raise ValueError('--ecr expects a list')
            for ecr in self.ecr:
                if not ecr.startswith('https'):
                    raise ValueError(
                        f'--ecr expects url endpoints: {ecr[:5]}***')

        if self.build_vars is None:
            self.build_vars = []
        else:
            # we are expecting: 'var1=value var2=value2' etc.
            # split into a list
            build_vars = [var.strip() for var in self.build_vars.split()]
            clean_vars = []
            for var in build_vars:
                neq = var.count('=')
                if neq != 1:
                    raise ValueError(
                        f'--build-var expects "var=value var2=value2": {var}')
                name, value = var.split('=', 1)
                if len(name) == 0 or len(value) == 0:
                    raise ValueError(
                        f'--build-var expects "var=value var2=value2": {var}')
                clean_vars.append(var)
            self.build_vars = clean_vars

    def run_with_args(self):
        """Run the requested commands"""
        # check the input
        self.check_input()

        # if we are exporting files; run and exit
        if self.export_locks:
            self.do_export_locks()
            return

        # do we need to build an image?
        time_tag = None
        if self.build:
            time_tag = datetime.now().strftime('%Y%m%d_%H%M')
            self.do_build(time_tag)

        # do we need to push images?
        if self.push:
            self.do_push(time_tag)

        # do we need a re-tag
        if self.retag:
            self.do_retag()

        # do ecr?
        if self.ecr is not None:
            self.do_ecr()

    def check_tags(self, *args):
        """Check the format of the tag. It should be a string
        without :

        Args
        ----
        *args: a list of string tags
        """
        for tag in args:
            if not isinstance(tag, str) or ':' in tag:
                raise ValueError(f'tag: {tag} has wrong format')

    def get_full_tag(self, image, tag):
        """Return full tag that includes the registry and repository

        Parameters:
        -----------
        image: str
            Image name (e.g. fornax-main or heasoft)
        tag: str
            The image tag.

        """
        self.check_tags(tag)
        full_tag = f"{self.repo}/{image}:{tag}"
        return full_tag

    def copy_common_files(self, destination):
        """Copy common files from the root folder"""
        if not self.dryrun and not (
            os.path.exists(destination) or
            os.path.exists(f'{destination}/Dockerfile')
        ):
            raise ValueError(f'image {destination} does not exists')

        # skip base images
        if destination not in ['fornax-slim']:
            return

        for file in COMMON_FILES:
            self.print(f"copying: {file} -> {destination}")
            if not self.dryrun:
                shutil.copy(file, os.path.join(destination, file))

    def extract_kernel_files(self):
        """Extract kernel files from the images to be used in fornax-slim
        """
        extra_args = self.extra_args or ''

        kernels_dir = 'fornax-slim/kernels'
        if os.path.exists(kernels_dir):
            shutil.rmtree(kernels_dir)
        self.run(f'mkdir -p {kernels_dir}', 100)

        for image in SOFTWARE_IMAGES:

            full_tag = self.get_full_tag(image, self.tag)

            self.print(f'exporting the kernel files for {image}')
            cmd = (
                'docker run --entrypoint="" --rm '
                f'-v $PWD/{kernels_dir}:/host '
                f'--user `id -u` {extra_args} '
                f"{full_tag} bash -c '"
                "cp -r /opt/jupyter/share/jupyter/kernels/* /host/'"
            )
            self.run(cmd, 10000)

            # if we are in github actions, always clean the images
            if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
                self.print(f'Cleaning docker image: {image}')
                cmd = f'docker rmi -f {full_tag}'
                self.run(cmd, 1000)

    def do_export_locks(self):
        """export the lock files from an image $LOCK_DIR/
        inside {image}:{tag}

        Needs:
        image: str
            image name, e.g. fornax-main, fornax-hea
        tag: str
            image tag, e.g. develop, stable etc.
        """
        for image in self.images:
            full_tag = self.get_full_tag(image, self.tag)

            lock_dir = f'{image}_locks'
            self.print(f' :: Exporting locks for {full_tag} to ./{lock_dir}')
            self.run(f'mkdir -p {lock_dir}', 100)
            cmd = (f'docker run --entrypoint="" --rm -v $PWD/{lock_dir}:/host '
                   f'--user `id -u` '
                   f"{full_tag} bash -c 'cp -r $LOCK_DIR/* /host/'")
            self.run(cmd, 1000)

    def do_build(self, time_tag):
        """Build an image by calling 'docker build ..'"""
        to_build = [im for im in IMAGE_ORDER if im in self.images]

        build_vars = self.build_vars

        for image in to_build:

            # make a copy so each image has its own set
            im_build_args = build_vars.copy()

            # add some defaults to build_args. For jupyter-base, the tags
            # are external and should be updated there
            if image != 'jupyter-base':
                mapping = dict(
                    REPOSITORY=self.repo,
                    BASE_TAG=self.tag,
                    BUILD_VERSION=f'{image}:{time_tag}'
                )
                for key, val in mapping.items():
                    exists = any([
                        arg.startswith(f'{key}=') for arg in im_build_args])
                    if not exists:
                        im_build_args.append(f'{key}={val}')

            # serialize the arguments
            cmd_args = ''
            for arg in im_build_args:
                if not arg.count("=") == 1:
                    raise ValueError(
                        f"build_args should be of the form 'name=value'. "
                        f"Got '{arg}'."
                    )
                name, val = arg.split("=", 1)
                cmd_args += f" --build-arg {name}={val}"

            # add any line arguments
            # now add any other line parameters
            if self.extra_args:
                cmd_args += f" {self.extra_args}"

            # now handle tags
            tags = [self.tag, time_tag]
            tags = [self.get_full_tag(image, tag) for tag in tags]
            cmd_args += ' '.join([f' --tag {tag}' for tag in tags])

            self.print(f"Building {tags[0]} ...")
            build_cmd = (
                f"docker build --platform=linux/amd64 {cmd_args} {image}")

            # For fornax-slim, extract the kernel files from other images
            # first. This will create kernels/
            if image == 'fornax-slim':
                self.extract_kernel_files()
                # copy common files
                self.copy_common_files(image)

            self.run(build_cmd, timeout=10000)

            # clean up kernels folder
            if image == 'fornax-slim':
                self.print("Cleaning kernels folder")
                self.run(f'rm -rf {image}/kernels', 1000)

    def do_push(self, time_tag=None):
        """Push an image to registry with 'docker push ..'"""
        to_push = [im for im in IMAGE_ORDER if im in self.images]

        for image in to_push:

            # add any line arguments
            # now add any other line parameters
            cmd_args = ''
            if self.extra_args:
                cmd_args += f" {self.extra_args}"

            tags = [self.tag]
            if time_tag is not None:
                tags.append(time_tag)
            tags = [self.get_full_tag(image, tag) for tag in tags]

            for tag in tags:
                push_cmd = f"docker push {tag}"
                self.print(f'Pushing {tag} ...')
                self.run(push_cmd, timeout=10000)

    def do_retag(self):
        """Release images by retagging them ..'"""
        images = self.images
        # if images is not gives, do all fornax-* images
        if images in (None, [], ''):
            images = [im for im in IMAGE_ORDER if im.startswith('fornax')]
        to_retag = [im for im in IMAGE_ORDER if im in images]

        for image in to_retag:
            source_tag = self.get_full_tag(image, self.tag)

            # pull
            command = f'docker pull {source_tag}'
            self.print(f"Pulling {source_tag} ...")
            self.run(command, timeout=3000)

            for retag in self.retag:
                new_tag = self.get_full_tag(image, retag)

                # tag
                command = f'docker tag {source_tag} {new_tag}'
                self.print(f"Tagging {source_tag} with {new_tag}")
                self.run(command, timeout=1000)

                # push
                command = f'docker push {new_tag}'
                self.print(f"Pushing {new_tag} ...")
                self.run(command, timeout=3000)

    def do_ecr(self):
        """Notify ECR endpoint with new images/tags ..'"""
        # Currently, only fornax-slim is in the ECR
        ecr_images = ['fornax-slim']
        if self.retag:
            images = ecr_images
        else:
            images = [im for im in ecr_images if im in self.images]
            if len(images) == 0:
                self.print('No images for ecr notification!')
                return

        # check the tags
        retag = [] if self.retag is None else self.retag
        self.check_tags(self.tag, *retag)

        # Loop through the images and collect parameters to params
        params = []
        for image in images:

            params.append([image, self.tag])

            # loog through any retag list
            if self.retag is not None:
                for retag in self.retag:
                    params.append([image, retag])

        # now loop through the parameters and make the request
        for image, tag in params:

            self.print(f"Triggering ecr for {image}, {tag} ...")

            for ipoint, endpoint in enumerate(self.ecr):
                if not self.dryrun:
                    url = f'{endpoint}?image={image}&tag={tag}'
                    request = urllib.request.Request(url)

                    # this will fail if something other than 404 is returned,
                    # and we want to know about it
                    try:
                        resp = urllib.request.urlopen(request)
                        self.print(f"Trigger returned status: {resp.status}")
                        self.print(("Trigger returned response: "
                                    f"{resp.read().decode()}"))
                        time.sleep(0.1)
                    except urllib.error.HTTPError as err:
                        # 404 means the repo does not exist, which is ok
                        if err.code == 404:
                            self.out("Trigger returned status: 404")
                        else:
                            # raise for any other error
                            raise


def main():
    """Main function"""
    ap = argparse.ArgumentParser()

    help = ("Space-separated image names. e.g 'fornax-base fornax-main'")
    ap.add_argument("images", nargs="*", help=help)

    help = ("tag name. Default current branch name")
    ap.add_argument("--tag", help=help)

    help = (f"Repositry name. Default: {DEFAULT_REPO}")
    ap.add_argument("--repo", help=help)

    help = ("Run the docker build?")
    ap.add_argument("--build", action="store_true", help=help, default=False)

    help = ("Push to registry after build?")
    ap.add_argument("--push", action="store_true", help=help, default=False)

    help = ("Release an image by retagging to the given tags")
    ap.add_argument("--retag", nargs='+', help=help)

    help = ("Export locks")
    ap.add_argument(
        "--export-locks",  action="store_true", help=help, default=False)

    help = ("ECR endpoints")
    ap.add_argument("--ecr", action='append', help=help)

    help = ("Extra arugments for docker build/run")
    ap.add_argument("--extra-args", help=help)

    help = ("Build variables for docker build, e.g. e.g. 'a=b c=d'")
    ap.add_argument("--build-vars", help=help)

    help = ("List software images. i.e. those with kernels that need export")
    ap.add_argument("--kernel-images", action='store_true', help=help)

    help = ("Print debug messages")
    ap.add_argument("--debug", action="store_true", help=help, default=False)

    help = ("Dry Run")
    ap.add_argument("--dryrun", action="store_true", help=help, default=False)

    # parse input arguments
    args = ap.parse_args()

    # soft-images does not need a builder
    if args.kernel_images:
        print(' '.join(SOFTWARE_IMAGES))

    builder = Builder(args)

    builder.input_summary()

    builder.run_with_args()


if __name__ == "__main__":
    main()
