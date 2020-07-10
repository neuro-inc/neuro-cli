import re
from typing import Callable
from uuid import uuid4

import click
from yarl import URL

from neuromation.api import RemoteImage
from neuromation.api.url_utils import CLUSTER_SCHEMES


URIFormatter = Callable[[URL], str]
ImageFormatter = Callable[[RemoteImage], str]


BOLD = re.compile(r"(?P<mark>\*\*|__)(?P<content>\S.*?\S)(?P=mark)")
EMPHASIS = re.compile(r"(?P<mark>\*|_)(?P<content>\S.*?\S)(?P=mark)")
INLINE_CODE = re.compile(r"`(?P<content>.*?)`")
CODE_BLOCK = re.compile(r"```(?P<content>.*?)```", re.DOTALL | re.MULTILINE)


def uri_formatter(username: str, cluster_name: str) -> URIFormatter:
    def formatter(uri: URL) -> str:
        if uri.scheme in CLUSTER_SCHEMES:
            if uri.host == cluster_name:
                assert uri.path[0] == "/"
                path = uri.path.lstrip("/")
                owner, _, rest = path.partition("/")
                if owner == username:
                    return f"{uri.scheme}:{rest.lstrip('/')}"
                return f"{uri.scheme}:/{path}"
        return str(uri)

    return formatter


def image_formatter(uri_formatter: URIFormatter) -> ImageFormatter:
    def formatter(image: RemoteImage) -> str:
        image_str = str(image)
        if image_str.startswith("image://"):
            return uri_formatter(URL(image_str))
        else:
            return image_str

    return formatter


def apply_styling(txt: str) -> str:
    REPLACES = {}

    # code blocks
    match = CODE_BLOCK.search(txt)
    while match is not None:
        label = f"REPLACE-CODE-BLOCK-{uuid4()}"
        lines = []
        first = True
        for line in match.group("content").splitlines():
            if first and not line:
                first = False
                continue
            lines.append(click.style(line, dim=True))
        REPLACES[label] = "\n".join(lines)
        txt = txt[: match.start()] + label + txt[match.end() :]
        match = CODE_BLOCK.search(txt)

    # inline codes
    match = INLINE_CODE.search(txt)
    while match is not None:
        label = f"REPLACE-INLINE-CODE-{uuid4()}"
        REPLACES[label] = click.style(match.group("content"), bold=True, dim=True)
        txt = txt[: match.start()] + label + txt[match.end() :]
        match = INLINE_CODE.search(txt)

    txt = BOLD.sub(click.style(r"\g<content>", bold=True), txt)
    txt = EMPHASIS.sub(click.style(r"\g<content>", underline=True), txt)
    for key, value in REPLACES.items():
        txt = txt.replace(key, value)
    return txt
