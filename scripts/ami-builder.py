
import requests
import argparse
import logging

# logging
logging.basicConfig(
    format="%(asctime)s|%(levelname)5s| %(message)s",
    datefmt="%Y-%m-%d|%H:%M:%S",
)

logger = logging.getLogger('::AMI-Builder::')
logger.setLevel(level=logging.DEBUG)


def main():
    """Main functions"""
    ap = argparse.ArgumentParser()

    ap.add_argument(
        'images', nargs='*',
        help=("Image names with tag to use separated by spaces e.g. "
              "'fornax-main:develop fornax-hea:develop'")
    )

    ap.add_argument(
        '--ssm-path',
        required=True,
        help='AMI tag to go in the SSM parameter (destination path)'
    )

    ap.add_argument(
        '--src',
        default=None,
        help=("Source ssm tag when copying; the target is --dst if given else --ssm-path")
    )

    ap.add_argument(
        '--dst',
        default=None,
        help=("Target ssm tag when copying; If not given use ssm-path")
    )

    ap.add_argument(
        '--endpoint',
        required=True,
        help='Trigger endpoint'
    )

    ap.add_argument(
        '--launch', action='store_true',
        help='Run the builder',
        default=False
    )

    args = ap.parse_args()

    # get parameters
    images = args.images
    launch = args.launch
    ssm_path = args.ssm_path
    src = args.src
    dst = args.dst
    ami_endpoint = args.endpoint

    logger.info(f'images: {images}')
    logger.info(f'passed ssm-path: {ssm_path}')
    logger.info(f'passed src: {src}')
    logger.info(f'passed dst: {dst}')
    logger.info(f'launch?: {launch}')
    logger.info(f'endpoint: ***')

    # ensure images have tags
    for image in images:
        if ':' not in image:
            raise ValueError(f'image {image} has not tag')

    # prepare parameters
    params = {
        'images': images,
        'ssm_path': ssm_path,
        'launch': launch
    }
    if src is not None:
        params['dst'] = dst if dst is not None else ssm_path
        params['src'] = src

    # params['version'] = 1.33  # eks version

    logger.info(f'Calling the builder with params ... {params}')
    req = requests.post(ami_endpoint, json=params)
    
    logger.info(f'status: {req.status_code}')
    logger.info(f'text: {req.text}')
    
    # raise for status != 200
    if req.status_code != 200:
        raise ValueError('Call returned with status != 200')

if __name__ == '__main__':
    main()