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

def _send(metric, value, kind):
    host = os.environ.get("HOSTIP")
    if not host:
        return
    line = (
        f"jupyter.startup.{metric},"
        f"pod_uid={os.environ.get('POD_UID', '')},"
        f"node={os.environ.get('NODE_NAME', '')},"
        f"user={os.environ.get('JUPYTERHUB_USER', '').translate(str.maketrans(',= :', '____'))}"
        f":{value}|{kind}\n"
    )
    try:
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(line.encode(), (host, 8125))
    except OSError:
        pass


if os.environ.get("HOSTIP"):
    try:
        now = time.time_ns()
        elapsed_ms = (now - int(os.environ.get("JUPYTER_LAST_NS") or now)) // 1_000_000
        _send("phase.duration_ms,phase=server_launch", elapsed_ms, "g")
        os.environ["JUPYTER_LAST_NS"] = str(now)
    except ValueError:
        pass

if not os.environ.get("HOSTIP"):
    os.environ.pop("JUPYTER_START_NS", None)
    os.environ.pop("JUPYTER_LAST_NS", None)

# Execute the command!
print("Executing: " + " ".join(command), flush=True)
try:
    os.execvp(command[0], command)
except OSError:
    _send("failures,phase=server_launch", 1, "c")
    raise
