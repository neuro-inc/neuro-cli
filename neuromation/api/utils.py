import sys
from typing import Any


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager  # noqa
else:
    from async_generator import asynccontextmanager  # noqa


class NoPublicConstructor(type):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("no public constructor")

    def _create(self, *args: Any, **kwargs: Any) -> Any:

        return super().__call__(*args, **kwargs)
