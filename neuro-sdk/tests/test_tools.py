import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, List
from unittest.mock import Mock, call

import pytest

from neuro_sdk import ConfigError, find_project_root
from neuro_sdk.utils import asyncgeneratorcontextmanager, queue_calls


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    project_root = tmp_path / "neuro-project"
    os.mkdir(project_root)
    with open(project_root / ".neuro.toml", "w"):
        pass
    return project_root


def test_find_root_in_root_dir(project_root: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.chdir(project_root)
        assert find_project_root() == project_root
    finally:
        os.chdir(old_workdir)


def test_find_root_in_subdir(project_root: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.mkdir(project_root / "foo")
        os.chdir(project_root / "foo")
        assert find_project_root() == project_root
    finally:
        os.chdir(old_workdir)


def test_find_root_uses_path_argument(project_root: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.chdir(project_root.parent)
        assert find_project_root(project_root) == project_root
    finally:
        os.chdir(old_workdir)


def test_find_root_not_in_project(tmp_path: Path) -> None:
    old_workdir = os.getcwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(ConfigError):
            find_project_root()
    finally:
        os.chdir(old_workdir)


async def test_queue_calls_saves_args(loop: asyncio.AbstractEventLoop) -> None:
    mock = Mock()

    class Foo:
        def bar(self, *args: Any, **kwargs: Any) -> None:
            mock(*args, **kwargs)

    queue, foo = queue_calls(Foo())
    args = (1, 2, 3)
    kwargs = dict(bar="baz")
    await foo.bar(*args, **kwargs)
    queued_call = await queue.get()
    queued_call()
    mock.assert_called_with(*args, **kwargs)


async def test_queue_calls_multiple_calls(loop: asyncio.AbstractEventLoop) -> None:
    calls_cnt = 5
    mock = Mock()

    class Foo:
        def bar(self, *args: Any, **kwargs: Any) -> None:
            mock(*args, **kwargs)

    queue, foo = queue_calls(Foo())
    for _ in range(calls_cnt):
        await foo.bar(42)
    while not queue.empty():
        queued_call = await queue.get()
        queued_call()
    mock.assert_has_calls([call(42) for _ in range(calls_cnt)])


async def test_queue_calls_attribute_error_for_non_existing_method() -> None:
    class Foo:
        pass

    queue, foo = queue_calls(Foo())
    with pytest.raises(AttributeError):
        await foo.bar()


async def test_queue_calls_type_error_for_not_method() -> None:
    class Foo:
        bar = "sss"

    queue, foo = queue_calls(Foo())
    with pytest.raises(TypeError):
        await foo.bar()


async def test_queue_calls_no_errors_for_none() -> None:
    queue, foo = queue_calls(None, allow_any_for_none=True)
    await foo.bar()
    await foo.baz()


async def test_asyncgeneratorcontextmanager() -> None:
    @asyncgeneratorcontextmanager
    async def mygen(err: bool = False) -> AsyncIterator[int]:
        logs.append("enter")
        try:
            yield 1
            if err:
                raise ValueError("my error")
            yield 2
        finally:
            logs.append("exit")
        logs.append("return")

    logs: List[str] = []
    res = []
    async with mygen() as it:
        async for x in it:
            res.append(x)
    assert res == [1, 2]
    assert logs == ["enter", "exit", "return"]

    logs = []
    res = []
    async with mygen(True) as it:
        with pytest.raises(ValueError, match="my error"):
            async for x in it:
                res.append(x)
            res = [x async for x in it]
    assert res == [1]
    assert logs == ["enter", "exit"]

    logs = []
    res = []
    with pytest.raises(TypeError, match="mygen"):
        async for x in mygen():  # type: ignore
            res.append(x)
    assert res == []
    assert logs == []
