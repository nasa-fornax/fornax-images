
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
        help=("Image names to use separated by spaces e.g. "
              "'fornax-main fornax-hea'")
    )

    ap.add_argument(
        '--eks',
        help=("EKS version to use. e.g. 1.33")
    )

    ap.add_argument(
        '--tag',
        required=True,
        help='AMI tag to produce'
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
    eks_version = args.eks
    launch = args.launch
    tag = args.tag
    ami_endpoint = args.endpoint

    logger.info(f'images: {images}')
    logger.info(f'eks_version: {eks_version}')
    logger.info(f'tag: {tag}')
    logger.info(f'launch?: {launch}')
    logger.info(f'endpoint: ***')

    # add the tag to the images
    for im in range(len(images)):
        if ':' not in images[im]:
            images[im] = f'{images[im]}:{tag}'

    # prepare parameters
    params = {
        'images': images,
        'tag': tag,
        'launch': launch
    }
    if eks_version is not None:
        params['version'] = eks_version
    logger.info('Calling the builder ...')
    req = requests.post(ami_endpoint, json=params)
    
    logger.info(f'status: {req.status_code}')
    logger.info(f'text: {req.text}')
    
    # raise for status != 200
    if req.status_code != 200:
        raise ValueError('Call returned with status != 200')

if __name__ == '__main__':
    main()