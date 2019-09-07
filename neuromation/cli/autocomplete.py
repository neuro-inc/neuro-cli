import json
import sys
import os
import socket
import struct
import tempfile
from pathlib import Path
from typing import List, Tuple

import click
from typing_extensions import TypedDict


CONFIG = "autocomplete.json"
SOCKNAME = "autocomplete.sock"


class Request(TypedDict):
    kind: str
    incomplete: str


def complete_job(
    ctx: click.Context, args: List[str], incomplete: str
) -> List[Tuple[str, str]]:
    return send_cmd({"kind": "job", "incomplete": incomplete})


def send_cmd(request: Request) -> List[Tuple[str, str]]:
    # todo: send calculated config path,
    # skip autocompletion if the path doesn't match default
    # to prevent leaking sensitive data
    bin_request = json.dumps(request).encode("uft-8")
    pre = struct.pack("<I", len(bin_request))
    maybe_start_server()
    with get_socket() as sock:
        sock.sendall(pre + bin_request)
        buf = sock.recv(4 * 4096)
        size, *tail = struct.unpack("<I", buf[:4])
        buf = buf[4:]
        while len(buf) < size:
            buf += sock.recv(4 * 4096)
        return json.loads(buf.decode("utf8"))


def maybe_start_server():
    folder = get_folder()
    try:
        # restrict the access to current user only
        folder.mkdir(0o700)
    except FileExistsError:
        pass
    try:
        with (folder / CONFIG).open() as f:
            config = json.load(f)
            pid = config["pid"]
            # check if the server is alive
            os.kill(pid, 0)
    except (OSError, TypeError, ValueError):
        # file not found or malformed,
        # or the server is stopped
        # restart the server
        pass

    sockname = folder / SOCKNAME
    if sockname.exists():
        sockname.unlink()

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(sockname))
    pass


def getid() -> str:
    return str(os.getsid(0))


def get_folder() -> Path:
    if sys.implementation.platform == "linux":
        # Linux has user-specific non-persistent location
        tmpdir = Path(f"/var/run/user/{os.getuid()}")
    else:
        tmpdir = Path(tempfile.gettempdir())
    sid = getid()
    return tmpdir / f"neuro-{sid}"


def get_socket() -> socket.socket:
    pass


def main():
    """Enrypoint for autocomplete sugesstion server."""

    pass
