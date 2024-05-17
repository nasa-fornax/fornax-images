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
import re
import json
import time
import logging
import sys

    

def build_images(image, dryrun, build_args, update_lock):
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
        if update_lock and len(glob.glob(f'{image}/conda-*-lock.yml')):
            # If update_lock, remove the old ones so the build does
            # not use them
            # TODO: handle individual files separately
            os.system(f'rm {image}/conda-*-lock.yml')
            
        out = subprocess.call(cmd)
        if out: 
            logging.error('\tError encountered.')
            sys.exit(1)

    # update lock-file?
    if update_lock:
        logging.debug(f'Updating the lock file for {image}')
        envfiles = [
            env for env in glob.glob(f'{image}/conda-*.yml') if 'lock' not in env
        ]
        for env in envfiles:
            match = re.match(rf'{image}/conda-(.*).yml', env)
            if match:
                env_name = match[1]
            else:
                env_name = 'base'
        # first create an env file
        cmd = [
            'docker', 'run', '--rm', 
            f'fornax/{image}:latest',
            'mamba', 'env', 'export', '-n', env_name
        ]
        logging.debug('\t' + (' '.join(cmd)))

        if not dryrun:
            out = subprocess.check_output(cmd)
            with open(f'{image}/tmp-{env_name}-lock.yml', 'wb') as fp:
                fp.write(out)

        # then call conda-lock on it
        # conda-lock -f tmp.yml -p linux-64 --lockfile tmp-lock.yml
        cmd = [
            'conda-lock', '-f', f'{image}/tmp-{env_name}-lock.yml',
            '-p', 'linux-64', '--lockfile', f'{image}/conda-{env_name}-lock.yml'
        ]
        logging.debug('\t' + (' '.join(cmd)))
        if not dryrun:
            out = subprocess.call(cmd)
            if out: 
                logging.error('\tError encountered.')
                sys.exit(1)
            os.system(f'rm {image}/tmp-{env_name}-lock.yml')

        # Now generate the packages-list.txt file that contain the list for reference
        cmd = [sys.executable, 'generate-package-list.py', f'{image}/conda-{env_name}-lock.yml']
        logging.debug('\t' + (' '.join(cmd)))
        if not dryrun:
            out = subprocess.check_output(cmd)
            with open(f'{image}/packages.txt', 'wb') as fp:
                fp.write(out)

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument('--dryrun', action='store_true', default=False)
    ap.add_argument('--update-lock', action='store_true', help='update conda lock file', default=False)
    ap.add_argument('image', help='image to build')
    ap.add_argument('--build-args', nargs='*', help='Extra arguments passed to docker build')
    args = ap.parse_args()


    logging.basicConfig(format='%(asctime)s|%(levelname)5s| %(message)s',
                        datefmt='%Y-%m-%d|%H:%M:%S')
    logging.getLogger().setLevel(logging.DEBUG)

    build_images(args.image, args.dryrun, args.build_args, args.update_lock)
