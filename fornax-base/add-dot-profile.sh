#!/bin/bash

# Add ~/.profile if it does not exist; which sources ~/.bashrc
# JL terminals source ~/.profile not ~/.bashrc
# But some user software may need ~/.bashrc (e.g. rust, julia)

if [ ! -f ~/.profile ]; then
    cat <<PROFILE > ~/.profile
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
PROFILE
fi