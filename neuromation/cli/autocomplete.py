import click
from typing import List, Tuple
from typing_extensions import TypedDict
import os
import socket
import json
import struct


class Request(TypedDict):
    kind: str
    incomplete: str


def complete_job(ctx: click.Context, args: List[str], incomplete: str) -> List[Tuple[str, str]]:
    return send_cmd({"kind": "job", "incomplete": incomplete})


def send_cmd(request: Request) -> List[Tuple[str, str]]:
    bin_request = json.dumps(request).encode('uft-8')
    pre = struct.pack('<I', len(bin_request))
    maybe_start_server()
    with get_socket() as sock:
        sock.sendall(pre+bin_request)
        buf = sock.recv(4*4096)
        size, *tail = struct.unpack('<I', buf[:4])
        buf = buf[4:]
        while len(buf) < size:
            buf += sock.recv(4*4096)
        return json.loads(buf.decode('utf8'))


def maybe_start_server():
    pass



def get_socket() -> socket.socket:
    pass
