from typing import Callable

from yarl import URL

from neuromation.api import RemoteImage
from neuromation.api.url_utils import CLUSTER_SCHEMES


URIFormatter = Callable[[URL], str]
ImageFormatter = Callable[[RemoteImage], str]


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
