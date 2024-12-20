# Content
This directory contains the docker image for HEAsoft.


# Building locally
To build the image locally, run the following from the top level of `fornax-images`:
```
version=6.32.1
docker build -t heasoft:$version --network=host --build-arg heasoft_version=$version heasoft/
```

# Building and pushing to the ECR Registry
This is done automatically by the CI once pushed to gitlab. 
Note that this `README.md` file is required for the CI to work.

# Versions
Version number is in `.image_tags`

- 6.32.1: Heasoft image that starts with `base_image-v0.1`
