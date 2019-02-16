import sys


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager  # noqa
else:
    from async_generator import asynccontextmanager  # noqa
