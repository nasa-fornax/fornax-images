#!/usr/bin/env python
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import os
import shlex
import socket
import sys
import time

# Entrypoint is start.sh
singleuser_exe = f"{os.environ['JUPYTER_DIR']}/bin/jupyterhub-singleuser"
command = [singleuser_exe]

# JupyterHub singleuser arguments are set using environment variables

# Append any optional NOTEBOOK_ARGS we were passed in.
# This is supposed to be multiple args passed on to the notebook command,
# so we split it correctly with shlex
if "NOTEBOOK_ARGS" in os.environ:
    command += shlex.split(os.environ["NOTEBOOK_ARGS"])

# Pass any other args we have been passed through
command += sys.argv[1:]

if os.environ.get("HOSTIP"):
    try:
        line = (
            f"jupyter_startup,pod_uid={os.environ.get('POD_UID', '')},"
            f"node={os.environ.get('NODE_NAME', '')},phase=exec v=1i {time.time_ns()}\n"
        )
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            line.encode(), (os.environ["HOSTIP"], 8094)
        )
    except OSError:
        pass

# Execute the command!
print("Executing: " + " ".join(command), flush=True)
os.execvp(command[0], command)
