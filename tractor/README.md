# Content

Main astrophysics demo image, containing tractor and related tools

Includes Firefly and Aladin for visualization

## To build and test

   $ docker build --rm --progress plain --force-rm -t tractor-image .

   $ docker run -it -p 9888:8888 --rm --name smce-tractor tractor-image:latest

Then open your browser tab to the localhost URL shown, replacing the port
8888 with 9888. You may have to reload the browser tab to get Jupyterlab
fully working.

