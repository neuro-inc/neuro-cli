import os
import re
import sys
from pathlib import Path
from typing import Sequence, Union

from yarl import URL


CLUSTER_SCHEMES = ("storage", "image", "job")


def uri_from_cli(
    path_or_uri: str,
    username: str,
    cluster_name: str,
    *,
    allowed_schemes: Sequence[str] = ("file", "storage"),
) -> URL:
    if "file" in allowed_schemes and path_or_uri.startswith("~"):
        path_or_uri = os.path.expanduser(path_or_uri)
        if path_or_uri.startswith("~"):
            raise ValueError(f"Cannot expand user for {path_or_uri}")
        path_or_uri = Path(path_or_uri).as_uri()

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
            f"Unsupported URI scheme: {uri.scheme}. "
            f"Please specify one of {', '.join(allowed_schemes)}."
        )
    if uri.scheme == "file":
        uri = normalize_local_path_uri(uri)
    elif uri.scheme == "blob":
        uri = normalize_blob_path_uri(uri, cluster_name)
    else:
        uri = _normalize_uri(uri, username, cluster_name)
    return uri


def normalize_storage_path_uri(uri: URL, username: str, cluster_name: str) -> URL:
    """Normalize storage url."""
    if uri.scheme != "storage":
        raise ValueError(
            f"Invalid storage scheme '{uri.scheme}:' (only 'storage:' is allowed)"
        )
    return _normalize_uri(uri, username, cluster_name)


def normalize_blob_path_uri(uri: URL, cluster_name: str) -> URL:
    """Normalize Blob Storage url."""
    if uri.scheme != "blob":
        raise ValueError(
            f"Invalid storage scheme '{uri.scheme}:' (only 'blob:' is allowed)"
        )

    stripped_path = uri.path.lstrip("/")
    # We treat all those as same URL's:
    #   blob:my_bucket/object_name
    #   blob:/my_bucket/object_name
    #   blob:///my_bucket/object_name
    # For full URL we require it to have cluster name as host:
    #   blob://my_cluster/my_bucket/object_name

    if not uri.host:
        if not stripped_path:
            raise ValueError(f"Bucket name is missing '{str(uri)}'")
        uri = URL.build(scheme=uri.scheme, host=cluster_name, path="/" + stripped_path)
    return uri


def _normalize_uri(resource: Union[URL, str], username: str, cluster_name: str) -> URL:
    """ Normalize all other user-bound URI's like jobs, storage, images, etc.
    """
    uri = resource if isinstance(resource, URL) else URL(resource)
    path = uri.path
    if (uri.host or path.lstrip("/")).startswith("~"):
        raise ValueError(f"Cannot expand user for {uri}")
    if not uri.host:
        if uri.scheme in CLUSTER_SCHEMES:
            host = cluster_name
            if path.startswith("/"):
                path = path.lstrip("/")
            else:
                path = f"{username}/{path}" if path else username
        else:
            raise ValueError(f"Absolute URI is required for scheme {uri.scheme}")
        uri = URL.build(scheme=uri.scheme, host=host, path="/" + path)

    return uri


def normalize_local_path_uri(uri: URL) -> URL:
    """Normalize local file url."""
    if uri.scheme != "file":
        raise ValueError(
            f"Invalid local file scheme '{uri.scheme}:' (only 'file:' is allowed)"
        )
    if uri.host:
        raise ValueError(f"Host part is not allowed, found '{uri.host}'")
    if uri.path.startswith("~"):
        raise ValueError(f"Cannot expand user for {uri}")
    path = _extract_path(uri)
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
