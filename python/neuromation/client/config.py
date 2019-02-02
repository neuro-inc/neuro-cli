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
