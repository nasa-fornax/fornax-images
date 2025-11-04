#!/usr/bin/env bash

action=$1
image=$2
tag=$3

if test -z $action || test -z $image; then
    echo "USAGE: $0 build|run image tag?"
    exit 1
fi

if test $action != "build" && test $action != "run"; then
    echo "ERROR: Unknown action $action. action needs to be either build or run"
    exit 1
fi

if test $action == "run" && test -z $tag; then 
    echo "ERROR: with action=run, a tag is needed; $0 build|run image tag"
    exit 1
fi

if test ! -d ./$image; then
    echo "ERROR: Unknown image $image."
    exit 1
fi

echo "========================"
echo "${action}ing $image:$tag"
echo "========================"


if test $action == "build"; then
    python scripts/build.py --extra-pars="--network=host" $image
fi

if test $action == "run"; then
    docker run -it --rm --network=host -v .:/tmp/code ghcr.io/nasa-fornax/fornax-images/$image:$tag bash
fi
