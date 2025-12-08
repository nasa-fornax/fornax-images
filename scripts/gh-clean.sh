#!/bin/bash

# remove packages from the gh action machine

rm -rf /usr/share/dotnet \
    /usr/local/lib/android \
    /usr/local/share/android-sdk \
    /usr/share/swift \
    /opt/hostedtoolcache/CodeQL \
    /opt/hostedtoolcache/* \
    /opt/ghc
docker image prune --all --force
docker builder prune -a

# apt
apt-get remove -y \
    firefox chromium-browser \
    ruby php nodejs
apt-get clean
rm -rf /var/lib/apt/lists/*