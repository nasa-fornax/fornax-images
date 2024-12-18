import argparse
import glob
import logging
import os
import re
import subprocess
import sys

# NB: we don't use docker-py because it doesn't support modern Dockerfiles

order = (
    "base_image",
    "tractor",
    #    "heasoft", # reenable heasoft once we have it packaged
)


class Base:
    # this class only exists (instead of module-level functions) to make unit
    # testing less painful; it is also used by "release.py"
    def __init__(self, logger):
        self.logger = logger

    def out(self, msg, severity=logging.INFO):
        self.logger.log(severity, msg)
        sys.stdout.flush()

    def run(self, command, timeout, **runargs):
        self.out(f"Running {command} with timeout {timeout}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            timeout=timeout,
            **runargs,
        )
        return result


class Builder(Base):
    def build(
        self,
        repository,
        path,
        tag,
        no_cache=False,
        build_args=None,
        plain=False,
    ):
        extra_args = []
        # cope with forks of the repository (see tractor/heasoft Dockerfiles) by
        # setting a build arg
        build_args = build_args or []
        default_tag = tag.rsplit(":", 1)[1]
        if not any([x.startswith("REPOSITORY=") for x in build_args]):
            build_args.append(f"REPOSITORY={repository}")
        if not any([x.startswith("BASE_IMAGE_TAG=") for x in build_args]):
            build_args.append(f"BASE_IMAGE_TAG={default_tag}")
        if not any([x.startswith("IMAGE_TAG=") for x in build_args]):
            build_args.append(f"IMAGE_TAG={default_tag}")

        for arg in build_args:
            if not arg.count("=") == 1:
                raise ValueError(
                    f"build_args should be of the form 'name=value'. "
                    f"Got '{arg}'."
                )
            name, val = arg.split("=", 1)
            nameandval = f"{name}={val}"
            extra_args.append(f"--build-arg {nameandval}")

        if no_cache:
            extra_args.append("--no-cache=true")
        if plain:
            extra_args.append("--progress=plain")
        extra_args = " ".join(extra_args)
        buildcommand = f"docker build {extra_args} --tag {tag} {path}"
        self.out(f"Building {path} via '{buildcommand}'")
        result = self.run(buildcommand, timeout=10000)
        self.out(result)

    def push(self, tag):
        pushcommand = f"docker push {tag}"
        self.out(f"Pushing {tag} via '{pushcommand}'")
        result = self.run(pushcommand, timeout=1000)
        self.out(result)

    def remove_lockfiles(self, path):
        self.out(f"Removing the lock files for {path}")
        lockfiles = glob.glob(f"{path}/conda-*lock.yml")
        for lockfile in lockfiles:
            self.out(f"Removing {path}/{lockfile}")
            os.unlink(lockfile)

    def update_lockfiles(self, path, repository, tag):
        tag = tag.rsplit(":", 1)[1]
        self.out(f"Updating the lock files for {path}")
        envfiles = glob.glob(f"{path}/conda-*.yml")
        envfiles = [
            env for env in glob.glob(f"{path}/conda-*.yml") if "lock" not in env
        ]
        for env in envfiles:
            match = re.match(rf"{path}/conda-(.*).yml", env)
            if match:
                env_name = match[1]
            else:
                env_name = "base"
            cmd = (
                f'docker run --entrypoint="" --rm '
                f"ghcr.io/{repository}/{path}:{tag} "
                f"mamba env export -n {env_name}"
            )

            result = self.run(cmd, 500, capture_output=True)
            lines = []
            include = False
            for line in result.stdout.split("\n"):
                if "name:" in line:
                    include = True
                if include:
                    lines.append(line)
            with open(f"{path}/conda-{env_name}-lock.yml", "w") as fp:
                fp.write("\n".join(lines))

    def builds_necessary(self, repository, tag, images):
        tobuild = []
        for name in images:
            if not name in order:
                self.out(f"Unknown image name {name}", logging.ERROR)
                raise SystemExit(2)

        # tractor and heasoft depend on base_image, so ordering is important
        # here (I think)
        for name in order:
            if name in images:
                struct = (
                    name,
                    f"ghcr.io/{repository}/{name}:{tag}",
                )
                tobuild.append(struct)

        return tobuild

    def chdir(self, path):
        os.chdir(path)


def main(
    builder,
    repository,
    tag=None,
    do_push=False,
    update_lock=False,
    no_cache=False,
    no_build=False,
    build_args=None,
    images=order,
    plain=False,
):
    if no_build and do_push:
        builder.out(
            "--no-build and --do-push cannot be used together", logging.ERROR
        )
        raise SystemExit(2)

    builder.out(f"Repository {repository}, tag {tag}")
    tobuild = builder.builds_necessary(repository, tag, images)

    # parent dir of the dir of this file (root of this checkout)
    here = __file__
    if not here.startswith(os.path.sep):
        here = os.path.join(os.getcwd(), here)

    root = os.path.dirname(os.path.dirname(here))
    builder.chdir(root)  # indirection for testing sanity

    for dockerdir, tag in tobuild:
        if not no_build:
            if update_lock:
                builder.remove_lockfiles(dockerdir)
            builder.build(
                repository, dockerdir, tag, no_cache, build_args, plain=plain
            )
        if update_lock:
            builder.update_lockfiles(dockerdir, repository, tag)
        if do_push:
            builder.push(tag)


if __name__ == "__main__":
    if not sys.version_info >= (3, 12):
        print("This script requires Python 3.12 or better")
        sys.exit(1)
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "repository", help="GH repository name (e.g. 'fornax-core/images')"
    )
    ap.add_argument("tag", help="CR tag name (e.g. 'branch-name')")
    ap.add_argument(
        "--push",
        action="store_true",
        help=(
            "After building, push to container registry (incompatible with "
            "--no-build)."
        ),
        default=False,
    )
    ap.add_argument(
        "--update-lock",
        action="store_true",
        help="update conda lock files (meant to be used when run locally to update conda lock files in local directories. A suitable command might be 'python3.12 buildimages.py nasa-fornax/fornax-images test --update-lock')",
        default=False,
    )
    ap.add_argument(
        "--no-cache",
        action="store_true",
        help="pass --no-cache to docker build",
        default=False,
    )
    ap.add_argument(
        "--no-build",
        action="store_true",
        help="don't actually build images (incompatible with --push)",
        default=False,
    )
    ap.add_argument(
        "--build-args",
        nargs="*",
        help=(
            "Extra --build-arg arguments passed to docker build e.g. 'a=b c=d'"
        ),
    )
    ap.add_argument(
        "--images",
        nargs="*",
        help=("Image names separated by spaces e.g. 'base_image tractor'"),
        default=order,
    )
    ap.add_argument(
        "--plain",
        action="store_true",
        help="Use plain progress output when running docker build",
        default=False,
    )

    args = ap.parse_args()

    # see https://github.com/docker/docker-py/issues/2230 for rationale
    # as to why we set DOCKER_BUILDKIT (--chmod flag to COPY)
    os.environ["DOCKER_BUILDKIT"] = "1"
    logging.basicConfig(
        format="%(asctime)s|%(levelname)5s| %(message)s",
        datefmt="%Y-%m-%d|%H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    builder = Builder(logger)

    main(
        builder,
        args.repository,
        args.tag,
        args.push,
        args.update_lock,
        args.no_cache,
        args.no_build,
        args.build_args,
        args.images,
        args.plain,
    )
