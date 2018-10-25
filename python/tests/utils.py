import json
from io import BytesIO
from unittest.mock import Mock

TRAIN_RESPONSE = {"status": "PENDING", "job_id": "iddqd"}


INFER_RESPONSE = {"status": "PENDING", "job_id": "iddqd"}


class Response:
    def __init__(self, payload, *, error=None):
        if type(payload) in [dict, list]:
            self.content_type = "application/json"
            self._text = json.dumps(payload)
            self._json = payload
        elif isinstance(payload, str):
            self.content_type = "text/plain"
            self._text = payload
        else:
            raise NotImplementedError(f"Unsupported type {type(payload)}")
        self._error = error

    async def json(self):
        return self._json

    async def text(self):
        return self._text

    def raise_for_status(self):
        if self._error:
            raise self._error


class JsonResponse(Response):
    def __init__(self, json, *, error=None):
        super().__init__(payload=json, error=error)


class PlainResponse(Response):
    def __init__(self, text, *, error=None):
        super().__init__(payload=text, error=error)


class BinaryResponse(Response):
    def __init__(self, data, *, error=None):
        self._stream = BytesIO(data)
        self.content_type = "application/octet-stream"
        self._error = error
        self.content = self

    async def read(self):
        return self._stream.read()

    async def readany(self):
        return self._stream.read()

    def raise_for_status(self):
        if self._error:
            raise self._error


def mocked_async_context_manager(return_value=None):
    class ContextManager:
        def __init__(self, *args, **kwargs):
            self._args = args

        async def __aenter__(self):
            return return_value

        async def __aexit__(self, *args):
            pass

    return Mock(wraps=ContextManager)
