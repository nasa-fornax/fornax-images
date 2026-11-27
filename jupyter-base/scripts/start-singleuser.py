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

def _emit(metric, value, **tags):
    """ Send one startup metric to telegraf's StatsD listener as a gauge. """
    host = os.environ.get("HOSTIP")
    if not host:
        return
    line = (
        f"jupyter.startup.{metric}"
        + "".join(f",{k}={v}" for k, v in tags.items())
        + f",pod_uid={os.environ.get('POD_UID', '')}"
        + f",node={os.environ.get('NODE_NAME', '')}"
        + f",user={os.environ.get('JUPYTERHUB_USER', '').translate(str.maketrans(',= :', '____'))}"
        + f":{value}|g\n"
    )
    try:
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(line.encode(), (host, 8125))
    except OSError:
        pass


def _phase_start():
    """Mark the start of a startup phase. Stores the current time in JUPYTER_PHASE_START_NS. """
    os.environ["JUPYTER_PHASE_START_NS"] = str(time.time_ns())


def _phase_end(phase):
    """Emit the duration of the current startup phase. Does nothing if that start time is missing. """
    try:
        elapsed_ms = (time.time_ns() - int(os.environ["JUPYTER_PHASE_START_NS"])) // 1_000_000
    except (KeyError, ValueError):
        return
    _emit("phase.duration_ms", elapsed_ms, phase=phase)


_phase_end("server_launch")
_phase_start()

if not os.environ.get("HOSTIP"):
    os.environ.pop("JUPYTER_START_NS", None)
    os.environ.pop("JUPYTER_PHASE_START_NS", None)

# Execute the command!
print("Executing: " + " ".join(command), flush=True)
os.execvp(command[0], command)
