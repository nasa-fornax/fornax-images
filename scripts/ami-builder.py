
import requests
import argparse
import logging
import os
import re

# logging
logging.basicConfig(
    format="%(asctime)s|%(levelname)5s| %(message)s",
    datefmt="%Y-%m-%d|%H:%M:%S",
)

logger = logging.getLogger('::AMI-Builder::')
logger.setLevel(level=logging.DEBUG)

def get_image_date_tag(image):
    """Use GH API to look up the data tag give a name tag
    
    Parameters:
    ----------
    image: str
        image from fornax-images repo of the form: image:tag
    
    """
    parts = image.split(':')
    if len(parts) != 2:
        raise ValueError(f'Expected image:tag, but got {image}')
    image = parts[0]
    input_tag = parts[1]

    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', None)
    if GITHUB_TOKEN is None:
        raise ValueError('GITHUB_TOKEN not defined')
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    session = requests.Session()

    # get all tags
    url = f'https://api.github.com/users/nasa-fornax/packages/container/fornax-images%2F{image}/versions'
    matched_tags = []
    while url and len(matched_tags) == 0:
        resp = session.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        for version in data:
            tags = version.get("metadata", {}).get("container", {}).get("tags", [])
            name = version.get('name', None)
            if input_tag in tags:
                matched_tags = tags
                break
        # pagination
        url = None
        if "Link" in resp.headers:
            links = resp.headers["Link"].split(",")
            for link in links:
                if 'rel="next"' in link:
                    url = link.split(";")[0].strip()[1:-1]
    
    pattern = re.compile(r"\d{8}_\d{4}")
    matches = [tag for tag in matched_tags if pattern.search(tag)]
    date_tag = matches[0] if len(matches) == 1 else None
    return date_tag



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
        '--endpoint', nargs='+',
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
    ami_endpoints = args.endpoint

    logger.info(f'passed images: {images}')
    logger.info(f'passed ssm-path: {ssm_path}')
    logger.info(f'passed src: {src}')
    logger.info(f'passed dst: {dst}')
    logger.info(f'launch?: {launch}')
    logger.info(f'endpoints: {len(ami_endpoints)}')

    # ensure images have tags
    for image in images:
        if ':' not in image:
            raise ValueError(f'image {image} has not tag')
    
    # Find the date tag for the passed images
    date_images = []
    for image in images:
        name, tag = image.split(':')
        date_tag = get_image_date_tag(image)
        if date_tag is None:
            raise ValueError(f'Cannot find a date tag for {image}')
        date_images.append(f'{name}:{date_tag}')

    # prepare parameters
    params = {
        'images': date_images,
        'ssm_path': ssm_path,
        'launch': launch
    }
    if src is not None:
        params['dst'] = dst if dst is not None else ssm_path
        params['src'] = src

    # params['version'] = 1.33  # eks version

    logger.info(f'Calling the builder with params ... {params}')
    for ie, ami_endpoint in enumerate(ami_endpoints):
        logger.info(f'Calling endpoint {ie+1}')
        req = requests.post(ami_endpoint, json=params)
    
    logger.info(f'status: {req.status_code}')
    logger.info(f'text: {req.text}')
    
    # raise for status != 200
    if req.status_code != 200:
        raise ValueError('Call returned with status != 200')

if __name__ == '__main__':
    main()