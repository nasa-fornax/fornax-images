#!/bin/bash
# This will be run as root inside Dockerfile

if test -f "apt.txt" ; then
    echo "Found apt.txt; using it ..."
    apt-get update --fix-missing > /dev/null
    xargs -a apt.txt apt-get install -y -q
    apt-get clean
    apt-get -y autoremove
    rm -rf /var/lib/apt/lists/*
fi