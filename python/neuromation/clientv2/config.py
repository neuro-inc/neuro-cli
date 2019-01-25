from pathlib import Path

from yarl import URL

from .users import get_token_username


class Config:
    def __init__(self, url: URL, token: str) -> None:
        self._url = url
        assert token, "Empty token is not allowed"
        self._token = token
        self._username = get_token_username(token)

    @property
    def url(self) -> URL:
        return self._url

    @property
    def token(self) -> str:
        return self._token

    @property
    def username(self) -> str:
        return self._username

    def norm_storage(self, uri: URL) -> URL:
        """Normalize storage url."""
        if uri.scheme != "storage":
            # TODO (asvetlov): change error text, mention storage:// prefix explicitly
            raise ValueError("Path should be targeting platform storage.")

        if uri.host == "~":
            uri = uri.with_host(self._username)
        elif not uri.host:
            uri = URL("storage://" + self._username + "/" + uri.path)
        return uri

    def norm_file(self, uri: URL) -> URL:
        """Normalize local file url."""
        if uri.scheme != "file":
            # TODO (asvetlov): change error text, mention file:// prefix explicitly
            raise ValueError("Path should be targeting local file system.")
        if uri.host:
            raise ValueError("Host part is not allowed")
        path = Path(uri.path)
        path = path.expanduser()
        path = path.resolve()
        return uri.with_path(str(path))
