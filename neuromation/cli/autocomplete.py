import json
import os
import socket
import struct
import tempfile
from pathlib import Path
from typing import List, Tuple

import click
from typing_extensions import TypedDict


class Request(TypedDict):
    kind: str
    incomplete: str


def complete_job(
    ctx: click.Context, args: List[str], incomplete: str
) -> List[Tuple[str, str]]:
    return send_cmd({"kind": "job", "incomplete": incomplete})


def send_cmd(request: Request) -> List[Tuple[str, str]]:
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
    pass


def getid() -> str:
    return str(os.getsid())


def getfolder() -> Path:
    sid = getid()
    ret = Path(tempfile.gettempdir()) / f"neuro-{sid}"
    try:
        ret.mkdir(0o700)
    except FileExistsError:
        if (ret / "autocomplete.json").exists():
            pass


def get_socket() -> socket.socket:
    pass
