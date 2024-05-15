#!/usr/bin/env python3

"""

Description:
------------
A python script for building docker images on sciserver.

"""

import argparse
import glob
import subprocess
import os
import json
import time
import logging
import sys

    

def build_images(image, dryrun, build_args, update_lock, lock_file):
    """call 'docker build' on each element in images

    Parameters
    ----------
    images: str
        The name of the image to build.
    dryrun: bool
        Print docker command without running.
    build_args: dict
        extra build arguments.
    update_lock: bool
        update lock file?
    lock_file: str
        name of the lock file
        
    """    
    
    # loop through requested images
    logging.debug(f'Working on image {image} ...')
    if os.path.exists(image) and os.path.exists(f'{image}/Dockerfile'):
        logging.debug(f'Found {image}/Dockerfile ...')
    else:    
        raise ValueError(f'No image folder found for {image}')

    # check build_args
    extra_args = []
    if build_args is not None:
        for arg in build_args:
            if '=' not in arg:
                raise ValueError(f'build_args should be of the form "name=value". Got "{arg}".')
        args = arg.split('=')
        args = f'{args[0].upper()}={args[1]}'
        extra_args = [i for arg in build_args for i in ['--build-arg', args]]
    
    # build the image #
    logging.debug(f'\tBuilding {image}')
    cmd = [
        'docker', 'build', '--network=host', '-t', 
        f'fornax/{image}:latest'
    ] + extra_args + [f'./{image}']
    logging.debug('\t' + (' '.join(cmd)))
    
    if not dryrun:
        if update_lock and os.path.exists(f'{image}/{lock_file}'):
            os.system(f'rm {image}/{lock_file}')
            
        out = subprocess.call(cmd)
        if out: 
            logging.error('\tError encountered.')
            sys.exit(1)

    # update lock-file?
    if update_lock:
        logging.debug(f'Updating the lock file for {image}')
        cmd = [
            'docker', 'run', '--rm', 
            f'fornax/{image}:latest',
            'mamba', 'env', 'export', '-f', f'{image}/{lock_file}'
        ]
        logging.debug('\t' + (' '.join(cmd)))

        if not dryrun:
            out = subprocess.call(cmd)

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument('--dryrun', action='store_true', default=False)
    ap.add_argument('--update-lock', action='store_true', help='update lock file', default=False)
    ap.add_argument('--lock_file', type=str, help='name of the lock file', default='environment-lock.yml')
    ap.add_argument('image', help='image to build')
    ap.add_argument('--build-args', nargs='*', help='Extra arguments passed to docker build')
    args = ap.parse_args()


    logging.basicConfig(format='%(asctime)s|%(levelname)5s| %(message)s',
                        datefmt='%Y-%m-%d|%H:%M:%S')
    logging.getLogger().setLevel(logging.DEBUG)

    build_images(args.image, args.dryrun, args.build_args, args.update_lock, args.lock_file)
