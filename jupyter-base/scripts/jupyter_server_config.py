# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# mypy: ignore-errors
import os
import socket
import stat
import subprocess
import time
from pathlib import Path

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.extension.manager import ExtensionManager
from jupyter_server.serverapp import ServerApp

c = get_config()  # noqa: F821


def _emit(phase):
    host = os.environ.get("HOSTIP")
    start = os.environ.get("JUPYTER_START_NS")
    if not host or not start:
        return
    try:
        elapsed_ms = (time.time_ns() - int(start)) // 1_000_000
        line = (
            f"fornax_metrics.jupyter.startup:{elapsed_ms}|ms|#phase:{phase},"
            f"pod_uid:{os.environ.get('POD_UID', '')},"
            f"node:{os.environ.get('NODE_NAME', '')}\n"
        )
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            line.encode(), (host, 8125)
        )
    except (OSError, ValueError):
        pass


_emit("server_config")

_load_all_extensions = ExtensionManager.load_all_extensions


def _load_all_extensions_emit(self):
    result = _load_all_extensions(self)
    _emit("ext_loaded")
    return result


ExtensionManager.load_all_extensions = _load_all_extensions_emit

_post_start = ServerApp._post_start


async def _post_start_emit(self):
    _emit("server_ready")
    os.environ.pop("JUPYTER_START_NS", None)
    await _post_start(self)


ServerApp._post_start = _post_start_emit

# Listen on all interfaces (ipv4 and ipv6)
c.ServerApp.ip = ""
c.ServerApp.open_browser = False

# to output both image/svg+xml and application/pdf plot formats in the notebook file
c.InlineBackend.figure_formats = {"png", "jpeg", "svg", "pdf"}

# https://github.com/jupyter/notebook/issues/3130
c.FileContentsManager.delete_to_trash = False

# Generate a self-signed certificate
OPENSSL_CONFIG = """\
[req]
distinguished_name = req_distinguished_name
[req_distinguished_name]
"""
if "GEN_CERT" in os.environ:
    dir_name = Path(jupyter_data_dir())
    dir_name.mkdir(parents=True, exist_ok=True)
    pem_file = dir_name / "notebook.pem"

    # Generate an openssl.cnf file to set the distinguished name
    cnf_file = Path(os.getenv("CONDA_DIR", "/usr/lib")) / "ssl/openssl.cnf"
    if not cnf_file.exists():
        cnf_file.write_text(OPENSSL_CONFIG)

    # Generate a certificate if one doesn't exist on a disk
    subprocess.check_call(
        [
            "openssl",
            "req",
            "-new",
            "-newkey=rsa:2048",
            "-days=365",
            "-nodes",
            "-x509",
            "-subj=/C=XX/ST=XX/L=XX/O=generated/CN=generated",
            f"-keyout={pem_file}",
            f"-out={pem_file}",
        ]
    )
    # Restrict access to the file
    pem_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    c.ServerApp.certfile = str(pem_file)

# Change default umask for all subprocesses of the Server if set in the environment
if "NB_UMASK" in os.environ:
    os.umask(int(os.environ["NB_UMASK"], 8))
