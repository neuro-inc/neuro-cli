from io import BytesIO
from unittest.mock import Mock

TRAIN_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'PENDING',
    'id': 'iddqd'
}


INFER_RESPONSE = {
    'results': 'schema://host/path',
    'status': 'PENDING',
    'id': 'iddqd'
}


class JsonResponse:
    def __init__(self, json):
        self._json = json
        self.content_type = 'application/json'


    async def json(self):
        return self._json


class BinaryResponse:
    def __init__(self, data):
        self._stream = BytesIO(data)
        self.content_type = 'application/octet-stream'

    async def read(self):
        return self._stream.read()


def mocked_async_context_manager(return_value=None):
    class ContextManager():
        def __init__(self, *args, **kwargs):
            self._args = args

        async def __aenter__(self):
            return return_value

        async def __aexit__(self, *args):
            pass

    return Mock(wraps=ContextManager)
