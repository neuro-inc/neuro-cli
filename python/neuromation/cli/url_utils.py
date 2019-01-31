import logging
from pathlib import Path

from yarl import URL


log = logging.getLogger(__name__)


def local_path_to_url(path: str) -> URL:
    abs_path = Path(path).expanduser().absolute()
    url = URL(f"file:{abs_path}")
    return url
