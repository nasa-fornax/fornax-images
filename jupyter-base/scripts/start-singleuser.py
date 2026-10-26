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
        now = time.time_ns()
        elapsed_ms = (now - int(os.environ.get("JUPYTER_START_NS") or now)) // 1_000_000
        line = (
            f"jupyter_startup,pod_uid={os.environ.get('POD_UID', '')},"
            f"node={os.environ.get('NODE_NAME', '')},phase=exec v={elapsed_ms}i {now}\n"
        )
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            line.encode(), (os.environ["HOSTIP"], 8094)
        )
    except (OSError, ValueError):
        pass

os.environ.pop("JUPYTER_START_NS", None)

# Execute the command!
print("Executing: " + " ".join(command), flush=True)
os.execvp(command[0], command)
