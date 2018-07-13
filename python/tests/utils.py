from io import BytesIO
from unittest.mock import Mock

TRAIN_RESPONSE = {
    'status': 'PENDING',
    'job_id': 'iddqd'
}


INFER_RESPONSE = {
    'status': 'PENDING',
    'job_id': 'iddqd'
}


class JsonResponse:
    def __init__(self, json, *, error=None):
        self._json = json
        self.content_type = 'application/json'
        self._error = error

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self._error:
            raise self._error


class PlainResponse:
    def __init__(self, text, *, error=None):
        self._text = text
        self.content_type = 'text/plain'
        self._error = error

    async def text(self):
        return self._text

    def raise_for_status(self):
        if self._error:
            raise self._error


class BinaryResponse:
    class StreamResponse:
        def __init__(self, data):
            self._stream = BytesIO(data)

        async def read(self):
            return self._stream.read()

        async def readany(self):
            return self._stream.read()

    def __init__(self, data, *, error=None):
        self._stream = BytesIO(data)
        self.content_type = 'application/octet-stream'
        self._error = error
        self._content = BinaryResponse.StreamResponse(data)

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        if self._error:
            raise self._error


def mocked_async_context_manager(return_value=None):
    class ContextManager():
        def __init__(self, *args, **kwargs):
            self._args = args

        async def __aenter__(self):
            return return_value

        async def __aexit__(self, *args):
            pass

    return Mock(wraps=ContextManager)
