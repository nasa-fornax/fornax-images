# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# mypy: ignore-errors
import importlib.metadata
import os
import socket
import stat
import subprocess
import time
from pathlib import Path

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.auth.decorator import allow_unauthenticated
from jupyter_server.base.handlers import APIVersionHandler
from jupyter_server.extension.manager import ExtensionManager
from jupyter_server.serverapp import ServerApp

c = get_config()  # noqa: F821


def _emit(metric, value, **tags):
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
    os.environ["JUPYTER_PHASE_START_NS"] = str(time.time_ns())


def _phase_end(phase):
    try:
        elapsed_ms = (time.time_ns() - int(os.environ["JUPYTER_PHASE_START_NS"])) // 1_000_000
    except (KeyError, ValueError):
        return
    _emit("phase.duration_ms", elapsed_ms, phase=phase)


def _startup_end():
    try:
        elapsed_ms = (time.time_ns() - int(os.environ["JUPYTER_START_NS"])) // 1_000_000
    except (KeyError, ValueError):
        return
    _emit("duration_ms", elapsed_ms)


def _time_extension(operation, name, fn, *args):
    started = time.perf_counter_ns()
    try:
        return fn(*args)
    finally:
        elapsed_ms = (time.perf_counter_ns() - started) // 1_000_000
        if elapsed_ms:
            _emit("extension.duration_ms", elapsed_ms, operation=operation, extension=name)


_phase_end("server_config")
_phase_start()

_add_extension = ExtensionManager.add_extension
_link_extension = ExtensionManager.link_extension
_load_extension = ExtensionManager.load_extension


def _add_extension_emit(self, extension_name, enabled=False):
    return _time_extension("import", extension_name, _add_extension, self, extension_name, enabled)


def _link_extension_emit(self, name):
    return _time_extension("link", name, _link_extension, self, name)


def _load_extension_emit(self, name):
    return _time_extension("load", name, _load_extension, self, name)


ExtensionManager.add_extension = _add_extension_emit
ExtensionManager.link_extension = _link_extension_emit
ExtensionManager.load_extension = _load_extension_emit

_init_server_extensions = ServerApp.init_server_extensions


def _init_server_extensions_emit(self):
    result = _init_server_extensions(self)
    _phase_end("extension_link")
    _phase_start()
    return result


ServerApp.init_server_extensions = _init_server_extensions_emit

_post_start = ServerApp._post_start


async def _post_start_emit(self):
    _phase_end("extension_load")
    _phase_start()
    await _post_start(self)


ServerApp._post_start = _post_start_emit

_api_version_get = APIVersionHandler.get


@allow_unauthenticated
def _api_version_get_emit(self):
    _phase_end("hub_ready")
    _startup_end()
    os.environ.pop("JUPYTER_START_NS", None)
    os.environ.pop("JUPYTER_PHASE_START_NS", None)
    return _api_version_get(self)


APIVersionHandler.get = _api_version_get_emit

_entry_points = importlib.metadata.entry_points
_server_proxy_entry_points = importlib.metadata.EntryPoints(
    importlib.metadata.EntryPoint(name=name, value=value, group="jupyter_serverproxy_servers")
    for name, value in [
        ("vscode", "jupyter_vscode_proxy:setup_vscode"),
        ("fviewer", "fviewer_labextension:start_viewer"),
    ]
)


def _entry_points_static_server_proxy(**params):
    if params == {"group": "jupyter_serverproxy_servers"}:
        return _server_proxy_entry_points
    return _entry_points(**params)


importlib.metadata.entry_points = _entry_points_static_server_proxy

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
