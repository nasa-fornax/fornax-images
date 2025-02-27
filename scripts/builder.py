import logging
import subprocess
import sys
import glob
import re
import urllib.request
import time


IMAGE_ORDER = (
    'base-image',
    # 'astro-default',
    # 'heasoft'
)


class TaskRunner:
    """Class for managing logging and system calls"""

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
        """Run system command {command} with a timeout

        Parameters:
        -----------
        command: str
            Command to pass to subprocess.run()
        timeout: int
            Timeout in sec
        **runargs:
            to be passed to subprocess.run

        Returns an instance of subprocess.CompletedProcess

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


class Builder(TaskRunner):
    """Class for managing the docker build commands"""

    def __init__(self, repository, logger, registry='ghcr.io', dryrun=False):
        """Create a new Builder

        Parameters:
        -----------
        repository: str
            Repository name. e.g. nasa-fornax/fornax-images
        logger: logging.Logger
            Logging object
        registry: str
            Name of the docker registry. Default: ghcr.io
        dryrun: bool
            If True, print the commands without running them

        """
        super().__init__(logger, dryrun)
        self.repository = repository
        self.registry = registry

    def _check_tags(self, source_tag=None, release_tags=None):
        """Check the source tags and/or release tags

        Parameters
        ----------
        source_tag: str or None
            the source tag
        release_tags: list or None
            A list of release tags
        """
        if source_tag is not None:
            if not isinstance(source_tag, str) or ':' in source_tag:
                raise ValueError(f'tag: {source_tag} is not a str without :')
        if release_tags is not None:
            if not isinstance(release_tags, list):
                raise ValueError(f'release_tags: {release_tags} is not a list')
            for release_tag in release_tags:
                if not isinstance(release_tag, str) or ':' in release_tag:
                    raise ValueError(
                        f'tag: {release_tag} is not a str without :')

    def get_full_tag(self, image, tag):
        """Return full tag that includes the registry and repository

        Parameters:
        -----------
        image: str
            Image name (e.g. astro-default or heasoft)
        tag: str
            The image tag.

        """
        self._check_tags(tag)
        full_tag = f'{self.registry}/{self.repository}/{image}:{tag}'
        return full_tag

    def build(self, image, tag, build_args=None, extra_args=None):
        """Build an image by calling 'docker build ..'

        Parameters:
        -----------
        repo: str
            repository name
        image: str
            The name of the image to be built (e.g. astro-default or heasoft)
        tag: str
            The image tag.
        build_args: list
            A list of str arguments to be passed directly to 'docker build'.
            e.g. 'SOME_ENV=myvalue OTHER_ENV=value'
        extra_args: str
            Extra command line arguments to be passed to 'docker build'
            e.g. '--no-cache --network=host'

        """
        cmd_args = []

        # build_args is a list
        build_args = build_args or []
        if not isinstance(build_args, list):
            raise ValueError(f'build_args is of type {type(build_args)}.'
                             ' Expected a list.')
        if ':' in tag:
            tag = tag.split(':')[-1]

        # Ensure we have: name=value
        build_args = [arg.strip() for arg in build_args]

        # add some defaults to build_args
        # For base-image, the tags are external and should be updated
        # in the Dockerfile
        if image != 'base-image':
            mapping = {
                'REPOSITORY': self.repository,
                'REGISTRY': self.registry,
                'BASE_TAG': tag,
            }
            for key, val in mapping.items():
                if not any([arg.startswith(f'{key}=') for arg in build_args]):
                    build_args.append(f'{key}={val}')

        # loop through the build_args and add them to cmd_args
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
        full_tag = self.get_full_tag(image, tag)
        build_cmd = f"docker build {cmd_args} --tag {full_tag} {image}"
        self.out(f"Building {image} ...")
        self.run(build_cmd, timeout=10000)

    def push(self, image, tag):
        """Push the image with 'docker push'

        Parameters:
        -----------
        image: str
            The name of Image to be pushed (e.g. astro-default or heasoft)
        tag: str
            The image tag.

        """
        full_tag = self.get_full_tag(image, tag)
        push_command = f'docker push {full_tag}'
        self.out(f"Pushing {full_tag} ...")
        self.run(push_command, timeout=1000)

    def release(self, source_tag, release_tags, images=None):
        """Make an image release by tagging the image with release_tags

        Parameters:
        -----------
        source_tag: str
            The tag name for the image (no repo name)
        release_tags: list
            A list of target tag names for the release (no repo name)
        images: list or None
            The list of images to tag for release. By default, all images

        """
        # check the passed tags
        self._check_tags(source_tag, release_tags)

        if images is not None and not isinstance(images, list):
            raise ValueError(f'Expected images to be a list; got {images}')

        # get a list of images to release
        to_release = images if images is not None else list(IMAGE_ORDER)
        for image in to_release:
            if image not in IMAGE_ORDER:
                raise ValueError(f'Unknow Requested image {image}.')

        # Loop through the images
        for image in to_release:
            full_source_tag = self.get_full_tag(image, source_tag)

            # pull
            command = f'docker pull {full_source_tag}'
            self.out(f"Pulling {full_source_tag} ...")
            self.run(command, timeout=1000)

            # loog through release tags
            for release_tag in release_tags:
                full_release_tag = self.get_full_tag(image, release_tag)

                # tag
                command = f'docker tag {full_source_tag} {full_release_tag}'
                self.out(f"Tagging {full_source_tag} with {full_release_tag}")
                self.run(command, timeout=1000)

                # push
                command = f'docker push {full_release_tag}'
                self.out(f"Pushing {full_release_tag} ...")
                self.run(command, timeout=1000)

    def push_to_ecr(
        self, endpoint, source_tag, release_tags=None, images=None
    ):
        """Trigger the ECR hook to update the images

        Parameters:
        -----------
        endpoint: str
            ECR endpoint
        source_tag: str
            The tag name for the image (no repo name)
        release_tags: list or None
            A list of target tag names for the release (no repo name)
        images: list or None
            The list of images to tag for release. By default, all images

        """
        # check the passed tags
        self._check_tags(source_tag, release_tags)

        if endpoint is None:
            raise ValueError('endpoint cannot be None')

        if images is not None and not isinstance(images, list):
            raise ValueError(f'Expected images to be a list; got {images}')

        # get a list of images to release
        images_to_process = images if images is not None else list(IMAGE_ORDER)
        for image in images_to_process:
            if image not in IMAGE_ORDER:
                raise ValueError(f'Unknow Requested image {image}.')

        # Loop through the images and collect parameters to params
        params = []
        for image in images_to_process:

            params.append([image, source_tag])

            # loog through release tags
            if release_tags is not None:
                for release_tag in release_tags:
                    params.append([image, release_tag])

        # now loop through the parameters and make the request
        for param in params:
            self.out(f"Triggering ecr for {image}, {source_tag} ...")
            if not self.dryrun:
                url = f'{endpoint}?image={image}&tag={source_tag}'
                request = urllib.request.Request(url)

                # this will fail if something doesn't work,
                # and we want to know about it
                with urllib.request.urlopen(request) as response:
                    self.out(f"Trigger returned status: {response.status}")
                    self.out(("Trigger returned response: "
                              f"{response.read().decode()}"))
                    time.sleep(5)

    def remove_lockfiles(self, image):
        """Remove conda lock files from an image

        Parameters
        ----------
        image: str
            Image name (e.g. astro-default or heasoft)
        """
        self.out(f"Removing the lock files for {image}")
        lockfiles = glob.glob(f"{image}/conda-*lock.yml")
        for lockfile in lockfiles:
            self.out(f"Removing {lockfile}")
            cmd = f'rm -f {lockfile}'
            self.run(cmd, timeout=100)

    def update_lockfiles(self, image, tag, extra_args=None):
        """Update the conda lock files in {image} using image {tag}

        Parameters
        ----------
        image: str
            The name of the image to be updated (e.g. astro-default or heasoft)
        tag: str
            The image tag.
        extra_args: str
            Extra command line arguments to be passed to 'docker run'
            e.g. '--network=host'

        """
        self._check_tags(tag)

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
            if result is not None:
                # dryrun=True
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
