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


def mocked_async_context_manager(return_value=None):
    class ContextManager():
        def __init__(self, *args, **kwargs):
            self._args = args

        async def __aenter__(self):
            return return_value

        async def __aexit__(self, *args):
            pass

    return Mock(wraps=ContextManager)
