#!/usr/bin/env python3

"""

Description:
------------
A python script for building docker images on fornax.

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
                'mamba', 'env', 'export', '-n', env_name,
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
    
            # Now generate the packages-list.txt file that contains the list for reference
            packages_file = f'{image}/packages-{env_name}.txt'
            logging.debug(f'Generating list of packages to {packages_file}')
            if not dryrun:
                generate_package_list(
                    lock_file=f'{image}/conda-{env_name}-lock.yml',
                    out_file=packages_file
                )

def _parse_package_url(line):
    """
    Parse a single conda-lock line and return name

    Supports both conda and pip pins.

    Returns name of package and version as tuple
    """

    if 'pythonhosted.org' in line: # pip
        # Get just the URL
        full_url = line.split()[-1]
        # Remove hash from URL
        url = full_url.split('#', 1)[0]
        # Get just the name of file we're getting
        filename = url.split('/')[-1]
        if filename.endswith('.whl'):
            # Wheels are in the format <package-name>-<version>-<tags>
            underscored_pkg_name, version, _ = filename.split('-', 2)
        elif filename.endswith('.tar.gz'):
            # tarballs are just <package>-<version_.tgz
            basename = filename.rsplit('.', 2)[0]
            underscored_pkg_name, version = basename.split('-', 1)
        else:
            raise RuntimeError(f'Found unknown file {filename} in conda-lock file')

        # PyPI has files with '_' when the package name has '-' in it
        pkg_name = underscored_pkg_name.replace('_', '-')
    else:
        # Given something like this:
        # https://conda.anaconda.org/conda-forge/noarch/nomkl-1.0-h5ca1d4c_0.tar.bz2#9a66894dfd07c4510beb6b3f9672ccc0
        # it should return nomkl, 1.0, h5ca14dc_0
        # Remove hash from the URL
        url = line.split('#', 1)[0]
        # Find last component of URL
        full_pkg = url.rsplit('/', 1)[-1]
        # Full pakage names are of form <pkg-name>-<version>-<build>.
        # Since <pkg-name> can have dashes, use rsplit to split the whole
        # thing into 3 components, starting from the right.
        pkg_name, version, _ = full_pkg.rsplit('-', 2)
    return pkg_name, version

def generate_package_list(lock_file, out_file):
    """Generate a reference list of pacakges from lock file

    Parameters
    ----------
    lock_file: str
        Name of lock file generated by conda-lock
    out_file: str
        Name of the output file
    
    """
    out_txt = '# List of packages and versions installed in the environment\n'
    out_txt += f'# Generated by parsing {lock_file}, please use that as source of truth\n'
    with open(lock_file) as fp:
        # Remove comments
        lines = [line for line in fp.readlines() if line.strip() and not line.startswith('#')]
    packages = []
    for line in lines:
        if 'url: https:' not in line:
            continue
        packages.append(_parse_package_url(line))
    # print sort listed of pacakges
    for pkg_name, version in sorted(packages):
       out_txt += f'{pkg_name}=={version}\n'

    with open(out_file, 'w') as fp:
        fp.write(out_txt)


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
