#!/bin/bash

# Add ~/.profile if it does not exist; which sources ~/.bashrc
# JL terminals source ~/.profile not ~/.bashrc
# But some user software may need ~/.bashrc (e.g. rust, julia)

if [ ! -f /home/$NB_USER/.profile ]; then
    cat <<PROFILE > /home/$NB_USER/.profile
if [ -f /home/$NB_USER/.bashrc ]; then
    source /home/$NB_USER/.bashrc
fi
PROFILE
fi