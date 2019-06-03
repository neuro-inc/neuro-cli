import re
import sys
from pathlib import Path
from typing import Sequence

from yarl import URL


def uri_from_cli(
    path_or_uri: str,
    username: str,
    *,
    allowed_schemes: Sequence[str] = ("file", "storage"),
) -> URL:
    uri = URL(path_or_uri)
    # len(uri.scheme) == 1 is a workaround for Windows path like C:/path/to.txt
    if not uri.scheme or len(uri.scheme) == 1:
        # Workaround for urllib.parse.urlsplit()'s strange behavior with
        # URLs like "scheme:123".
        if re.fullmatch(r"[a-zA-Z0-9+\-.]{2,}:[0-9]+", path_or_uri):
            uri = URL(f"{path_or_uri}#")
        elif "file" in allowed_schemes:
            if re.fullmatch(r"[0-9]+", path_or_uri):
                uri = URL(f"file:{path_or_uri}#")
            else:
                uri = URL(f"file:{path_or_uri}")
    if not uri.scheme:
        raise ValueError(
            f"URI Scheme not specified. "
            f"Please specify one of {', '.join(allowed_schemes)}."
        )
    if uri.scheme not in allowed_schemes:
        raise ValueError(
            f"Unsupported URI scheme: {uri.scheme or 'Empty'}. "
            f"Please specify one of {', '.join(allowed_schemes)}."
        )
    if uri.scheme == "file":
        uri = normalize_local_path_uri(uri)
    else:
        uri = _normalize_uri(uri, username)
    return uri


def normalize_storage_path_uri(uri: URL, username: str) -> URL:
    """Normalize storage url."""
    if uri.scheme != "storage":
        raise ValueError(
            f"Invalid storage scheme '{uri.scheme}://' "
            "(only 'storage://' is allowed)"
        )
    return _normalize_uri(uri, username)


def _normalize_uri(uri: URL, username: str) -> URL:
    path = uri.path
    if not uri.host:
        if path.startswith("~"):
            raise ValueError(f"Cannot expand user for {uri}")
        if not path.startswith("/"):
            uri = URL(f"{uri.scheme}://{username}/{path}")
        else:
            path = uri.path.lstrip("/")
            if path:
                uri = URL(f"{uri.scheme}://{path}")
    if uri.host == "~":
        uri = uri.with_host(username)
    elif uri.host and uri.host.startswith("~"):
        raise ValueError(f"Cannot expand user for {uri}")

    path = uri.path
    if path.startswith("/"):
        path = uri.path.lstrip("/")
        if path or uri.host:
            uri = uri.with_path(path)

    return uri


def normalize_local_path_uri(uri: URL) -> URL:
    """Normalize local file url."""
    if uri.scheme != "file":
        raise ValueError(
            f"Invalid local file scheme '{uri.scheme}://' "
            "(only 'file://' is allowed)"
        )
    if uri.host:
        raise ValueError(f"Host part is not allowed, found '{uri.host}'")
    path = _extract_path(uri)
    path = path.expanduser()
    if path.parents and str(path.parents[0]).startswith("~"):
        raise ValueError(f"Cannot expand user for {uri}")
    # path.absolute() does not work with relative path with disk
    # See https://bugs.python.org/issue36305
    path = Path(path.anchor).resolve() / path
    ret = URL(path.as_uri())
    while ret.path.startswith("//"):
        ret = ret.with_path(ret.path[1:])
    return ret


def _extract_path(uri: URL) -> Path:
    path = Path(uri.path)
    if sys.platform == "win32":
        # result of previous normalization
        if re.match(r"^[/\\][A-Za-z]:[/\\]", str(path)):
            return Path(str(path)[1:])
    return path
