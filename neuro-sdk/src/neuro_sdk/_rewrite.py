from typing import TypeVar

_T = TypeVar("_T")


def rewrite_module(obj: _T) -> _T:
    obj.__module__ = "neuro_sdk"
    return obj
