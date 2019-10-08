import logging
from typing import Any

import aiohttp
import pytest

from neuromation.api.utils import retries


async def test_success(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    for retry in retries("Fails", attempts=5):
        async with retry:
            count += 1

    assert count == 1
    assert caplog.record_tuples == []


async def test_first_fails(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    for retry in retries("Fails", attempts=5):
        async with retry:
            count += 1
            if count == 1:
                raise aiohttp.ClientError

    assert count == 2
    assert caplog.record_tuples == [
        ("neuromation.api.utils", logging.INFO, "Fails: .  Retry...")
    ]


async def test_two_fail(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    for retry in retries("Fails", attempts=5):
        async with retry:
            count += 1
            if count <= 2:
                raise aiohttp.ClientError

    assert count == 3
    assert (
        caplog.record_tuples
        == [("neuromation.api.utils", logging.INFO, "Fails: .  Retry...")] * 2
    )


async def test_all_fail(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    with pytest.raises(aiohttp.ClientError):
        for retry in retries("Fails", attempts=5):
            async with retry:
                count += 1
                raise aiohttp.ClientError

    assert count == 5
    assert (
        caplog.record_tuples
        == [("neuromation.api.utils", logging.INFO, "Fails: .  Retry...")] * 4
    )


async def test_unexpected_error(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    with pytest.raises(ZeroDivisionError):
        for retry in retries("Fails", attempts=5):
            async with retry:
                count += 1
                1 / 0

    assert count == 1
    assert caplog.record_tuples == []
