import logging
import os
import sys
import argparse
import json

sys.path.insert(0, os.getcwd())
from builder import Builder, IMAGE_ORDER  # noqa 402

if __name__ == '__main__':

    ap = argparse.ArgumentParser()

    ap.add_argument(
        'images', nargs='*',
        help=("Image names to build separated by spaces e.g. "
              "'base-image astro-default'")
    )

    ap.add_argument(
        '--tag',
        help=("Container registry tag name (e.g. 'mybranch'). "
              "Default is current git branch")
    )

    ap.add_argument(
        '--registry',
        help='Container registry name (e.g. ghcr.io)',
        default='ghcr.io'
    )

    ap.add_argument(
        '--repository',
        help="GH repository name (e.g. 'nasa-fornax/fornax-images')",
        default='nasa-fornax/fornax-images'
    )

    ap.add_argument(
        '--push', action='store_true',
        help='After building, push to container registry',
        default=False
    )

    ap.add_argument(
        '--release', nargs='*',
        help='Release using the given tag'
    )

    ap.add_argument(
        '--trigger-ecr', action='store_true',
        help='Trigger the ECR webhook',
        default=False
    )

    ap.add_argument(
        '--ecr-endpoint',
        help='endpoint to trigger the push to the ECR'
    )

    ap.add_argument(
        '--no-build', action='store_true',
        help="Do not run 'docker build' command",
        default=False
    )

    ap.add_argument(
        '--update-lock', action='store_true',
        help='Update conda lock files.',
        default=False
    )

    ap.add_argument(
        '--dryrun', action='store_true',
        help='prepare but do not run commands',
        default=False
    )

    ap.add_argument(
        '--build-args', nargs='*',
        help="Extra --build-arg arguments for docker build e.g. 'a=b c=d'"
    )

    ap.add_argument(
        '--extra-pars',
        help="Arguments to be passed to `docker build` or `docker run`",
        default=None
    )

    ap.add_argument(
        '--debug', action='store_true',
        help='Print debug messages',
        default=False
    )

    args = ap.parse_args()

    # get parameters
    dryrun = args.dryrun
    debug = args.debug
    images = args.images
    registry = args.registry
    repository = args.repository
    tag = args.tag
    push = args.push
    release = args.release
    trigger_ecr = args.trigger_ecr
    ecr_endpoint = args.ecr_endpoint
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
    builder = Builder(repository, logger, dryrun=dryrun, registry=registry)

    # get current branch name as default tag
    if (len(images) or release is not None) and tag is None:
        out = builder.run(
            'git branch --show-current', timeout=100, capture_output=True
        )
        if out is not None:
            tag = out.stdout.strip()
        # if out is None, we are in --dryrun mode, add a dummy tag
        tag = 'no-tag' if out is None else out.stdout.strip()

    # some logging:
    builder.out('Builder initialized ..', logging.DEBUG)
    builder.out('+++ INPUT +++', logging.DEBUG)
    builder.out(f'images: {images}', logging.DEBUG)
    builder.out(f'registry: {registry}', logging.DEBUG)
    builder.out(f'repository: {repository}', logging.DEBUG)
    builder.out(f'tag: {tag}', logging.DEBUG)
    builder.out(f'push: {push}', logging.DEBUG)
    builder.out(f'release: {release}', logging.DEBUG)
    builder.out(f'update_lock: {update_lock}', logging.DEBUG)
    builder.out(f'no_build: {no_build}', logging.DEBUG)
    builder.out(f'build_args: {build_args}', logging.DEBUG)
    builder.out(f'extra_pars: {extra_pars}', logging.DEBUG)
    builder.out('+++++++++++++', logging.DEBUG)

    # if releasing, tag all images
    if release is not None:
        images = list(IMAGE_ORDER)

    # get a sorted list of images to build
    to_build = []
    for image in IMAGE_ORDER:
        if image in images:
            to_build.append(image)

    builder.out(f'Images to build: {to_build}', logging.DEBUG)
    for image in to_build:
        builder.out(f'Working on: {image}', logging.DEBUG)

        # if we are tagging to main; do not build
        # just re-tag from the latest develop
        if tag == 'main':
            builder.release('develop', 'main', images)
            continue

        if update_lock:
            builder.remove_lockfiles(image)

        if not no_build:
            builder.build(image, tag, build_args, extra_pars)

        if update_lock:
            builder.update_lockfiles(image, tag)

        if push:
            builder.push(image, tag)

    if release is not None:
        builder.release(tag, release, images)

    if trigger_ecr:
        builder.push_to_ecr(ecr_endpoint, tag, release, images)
