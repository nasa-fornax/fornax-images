import logging
import subprocess
import sys
import os
import glob
import re
import argparse
import json

IMAGE_ORDER = (
    'base_image',
    'astro-default',
    #'heasoft'
)

class Builder:
    """Base class for running system commands and logging

    this class only exists (instead of module-level functions) to make unit
    testing less painful; it is also used by "release.py"
    """
    def __init__(self, logger, dryrun=False):
        """Create a new TaskRunner
        
        Parameters:
        -----------
        logger: logging.Logger
            Logging object
        dryrun: bool
            If True, print the commands without running them
        
        """
        self.logger = logger
        self.dryrun = dryrun

    def out(self, msg, severity=logging.INFO):
        """Log progress message
        
        Parameters
        ----------
        msg: str
            Message to log
        severity: int
            Logging level: logging.INFO, DEBUG, ERROR etc.

        """
        self.logger.log(severity, msg)
        sys.stdout.flush()

    def run(self, command, timeout, **runargs):
        """Run system command {command}
        
        Parameters:
        -----------
        command: str
            Command to pass to subprocess.run()
        timout: int
            Timeout in sec
        **runargs:
            to be passed to subprocess.run
        
        """
        self.out(f"Running ::\n{command}")
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
    
    def build(self, repo, image, tag, build_args=None, extra_args=None):
        """Build an image by called 'docker build'
        
        Parameters:
        -----------
        repo: str
            repository name
        image: str
            path to the image folder (e.g. astro-default or heasoft)
        tag: str
            a tag name for the image
        build_args: list
            A list of str arguments to be passed directly to 'docker build'. e.g.
            'SOME_ENV=myvalue'
        extra_args: str
            Extra command line arguments to be passed to 'docker build'
            e.g. '--no-cache --network=host'
        
        """
        cmd_args = []
    
        # build_args is a list
        build_args = build_args or []
        if not isinstance(build_args, list):
            raise ValueError(f'build_args is of type {type(build_args)}. Expected a list.')
        full_tag = tag
        if ':' in tag:
            tag = tag.rsplit(':', 1)[1]
        
        # Ensure we have: name=value
        build_args = [arg.strip() for arg in build_args]
        
        # add passed parameters to build_args
        mapping = {
            'REPOSITORY': repo,
            'IMAGE_TAG': tag,
        }
        for key,val in mapping.items():
            if not any([arg.startswith(f'{key}=') for arg in build_args]):
                build_args.append(f'{key}={val}')

        # loop through the build_args and add them extra_args
        for arg in build_args:
            if not arg.count("=") == 1:
                raise ValueError(
                    f"build_args should be of the form 'name=value'. "
                    f"Got '{arg}'."
                )
            name, val = arg.split("=", 1)
            cmd_args.append(f"--build-arg {name}={val}")

        # now add any other line parameters
        if extra_args:
            cmd_args.append(extra_args)

        cmd_args = " ".join(cmd_args)
        build_cmd = f"docker build {cmd_args} --tag {full_tag} {image}"
        self.out(f"Building {image} ...")
        result = self.run(build_cmd, timeout=10000)

    def push(self, tag):
        """Push the image with 'docker push'
        
        Parameters:
        -----------
        tag: str
            a tag name for the image of the form: repo:tag

        """
        if not isinstance(tag, str) or ':' not in tag:
            raise ValueError(f'tag: {tag} is not a str the form repo:tag')
        push_command = f'docker push {tag}'
        self.out(f"Pushing {tag} ...")
        result = self.run(push_command, timeout=1000)
    
    def release(self, repo, source_tag, release_tags):
        """Push the image with 'docker push'
        
        Parameters:
        -----------
        repo: str
            repo name
        source_tag: str
            The tag name for the image (no repo name)
        release_tags: list
            A list of target tag names for the release (no repo name)

        """
        if not isinstance(source_tag, str) or ':' in source_tag:
            raise ValueError(f'source_tag: {source_tag} is expected to be a str with no repo')
        if not isinstance(release_tags, list):
            raise ValueError(f'release_tags: {release_tags} is not a list')
        for release_tag in release_tags:
            if not isinstance(release_tag, str) or ':' in release_tag:
                raise ValueError(f'release_tag: {release_tag} is expected to be a str with no repo')
        # Loop through the images
        for image in IMAGE_ORDER:
            sourcetag = f'ghcr.io/{repo}/{image}:{source_tag}'
            # pull
            command = f'docker pull {sourcetag}'
            self.out(f"Pulling {sourcetag} ...")
            self.run(command, timeout=1000)
            for release_tag in release_tags:
                releasetag = f'ghcr.io/{repo}/{image}:{release_tag}'
                # tag
                command = f'docker tag {sourcetag} {releasetag}'
                self.out(f"Tagging {sourcetag} with {releasetag} ...")
                self.run(command, timeout=1000)
                # pull
                command = f'docker push {releasetag}'
                self.out(f"Pushing {releasetag} ...")
                self.run(command, timeout=1000)

    def remove_lockfiles(self, image):
        """Remove conda lock files from image
        
        Parameters
        ----------
        image: str
            name of the image folder containing Dockerfile and lockfiles if any.
        """
        self.out(f"Removing the lock files for {image}")
        lockfiles = glob.glob(f"{image}/conda-*lock.yml")
        for lockfile in lockfiles:
            self.out(f"Removing {lockfile}")
            cmd = f'rm -f {lockfile}'
            result = self.run(cmd, timeout=100)

    def update_lockfiles(self, image, tag, extra_args=None):
        """Update the conda lock files in {image} using image {tag}
        
        Parameters
        ----------
        image: str
            path to the image folder (e.g. astro-default or heasoft)
        tag: str
            a tag name for the image of the form: repo:tag
        extra_args: str
            Extra command line arguments to be passed to 'docker run'
            e.g. '--network=host'
        """
        if not isinstance(tag, str) or ':' not in tag:
            raise ValueError(f'tag: {tag} is not a str the form repo:tag')

        extra_args = extra_args or ''
        if not isinstance(extra_args, str):
            raise ValueError(f'Expected str for extra_args; got: {extra_args}')

        self.out(f'Updating the lock files for {image}')
        envfiles = [env for env in glob.glob(f'{image}/conda-*.yml')
                    if 'lock' not in env]
        for env in envfiles:
            match = re.match(rf"{image}/conda-(.*).yml", env)
            env_name = match[1] if match else 'base'
            cmd = (f'docker run --entrypoint="" --rm {extra_args} {tag} '
                   f'mamba env export -n {env_name}')
            result = self.run(cmd, 500, capture_output=True)
            if result is not None: # dryrun=True
                # capture lines after: 'name:'
                lines = []
                include = False
                for line in result.stdout.split('\n'):
                    if "name:" in line:
                        include = True
                    if include:
                        lines.append(line)
                with open(f"{image}/conda-{env_name}-lock.yml", "w") as fp:
                    fp.write("\n".join(lines))

if __name__ == '__main__':
    
    ap = argparse.ArgumentParser()

    ap.add_argument('images', nargs='*',
        help="Image names to build separated by spaces e.g. 'base_image astro-default'")

    ap.add_argument('--tag',
        help="Container registry tag name (e.g. 'mybranch'). Default is current git branch")

    ap.add_argument('--registry',
        help='Container registry name (e.g. ghcr.io)',
        default='ghcr.io')

    ap.add_argument('--repository',
        help="GH repository name (e.g. 'nasa-fornax/fornax-images')",
        default='nasa-fornax/fornax-images')

    ap.add_argument('--push', action='store_true',
        help='After building, push to container registry',
        default=False)
    
    ap.add_argument('--release', nargs='*',
        help='Release using the given tag')
    
    ap.add_argument('--no-build', action='store_true',
        help="Do not run 'docker build' command",
        default=False)

    ap.add_argument('--update-lock', action='store_true',
        help='Update conda lock files.',
        default=False)

    ap.add_argument('--dryrun', action='store_true',
        help='prepare but do not run commands',
        default=False)

    ap.add_argument('--build-args', nargs='*',
        help="Extra --build-arg arguments passed to docker build e.g. 'a=b c=d'")

    ap.add_argument('--extra-pars',
        help="Arguments to be passed directly to `docker build` or `docker run`",
        default=None)
    
    ap.add_argument('--debug', action='store_true',
        help='Print debug messages',
        default=False)

    args = ap.parse_args()
    
    # get parameters
    dryrun = args.dryrun
    debug = args.debug
    images = args.images
    registry = args.registry
    repo = args.repository
    tag = args.tag
    push = args.push
    release = args.release
    update_lock = args.update_lock
    no_build = args.no_build
    build_args = args.build_args
    extra_pars = args.extra_pars

    # in case images is of the form: '["dir_1", "dir_2"]'
    if len(images) == 1 and '[' in images[0]:
        images = json.loads(images[0])

    os.environ["DOCKER_BUILDKIT"] = "1"
    logging.basicConfig(
        format="%(asctime)s|%(levelname)5s| %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )

    logger = logging.getLogger('::Builder::')
    logger.setLevel(level=logging.DEBUG if debug else logging.INFO)
    builder = Builder(logger, dryrun=dryrun)

    # get current branch name as default tag
    if (len(images) or release is not None) and tag is None:
        out = builder.run('git branch --show-current', timeout=100, capture_output=True)
        if out is not None:
            tag = out.stdout.strip()
        # if out is None, we are in --dryrun mode, add a dummy tag
        tag = 'no-tag' if out is None else out.stdout.strip()
    
    # some logging:
    builder.out('Builder initialized ..', logging.DEBUG)
    builder.out('+++ INPUT +++', logging.DEBUG)
    builder.out(f'images: {images}', logging.DEBUG)
    builder.out(f'registry: {registry}', logging.DEBUG)
    builder.out(f'repository: {repo}', logging.DEBUG)
    builder.out(f'tag: {tag}', logging.DEBUG)
    builder.out(f'push: {push}', logging.DEBUG)
    builder.out(f'release: {release}', logging.DEBUG)
    builder.out(f'update_lock: {update_lock}', logging.DEBUG)
    builder.out(f'no_build: {no_build}', logging.DEBUG)
    builder.out(f'build_args: {build_args}', logging.DEBUG)
    builder.out(f'extra_pars: {extra_pars}', logging.DEBUG)
    builder.out('+++++++++++++', logging.DEBUG)

    # get a sorted list of images to build
    to_build = []
    for image in IMAGE_ORDER:
        if image in images:
            to_build.append(image)

    builder.out(f'Images to build: {to_build}', logging.DEBUG)
    for image in to_build:
        builder.out(f'Working on: {image}', logging.DEBUG)

        full_tag = f'{registry}/{repo}/{image}:{tag}'
        
        if update_lock:
            builder.remove_lockfiles(image)
        
        if not no_build:
            builder.build(repo, image, full_tag, build_args, extra_pars)
        
        if update_lock:
            builder.update_lockfiles(image, full_tag)

        if push:
            builder.push(full_tag)
        
    if release is not None:
        builder.release(repo, tag, release)
