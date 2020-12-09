import logging
from typing import Any

import aiohttp
import pytest

from neuro_sdk.utils import retries


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
                raise aiohttp.ClientError("Ouch!")

    assert count == 2
    record = ("neuro_sdk.utils", logging.INFO, "Fails: Ouch!.  Retry...")
    assert caplog.record_tuples == [record]


async def test_two_fail(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    for retry in retries("Fails", attempts=5):
        async with retry:
            count += 1
            if count <= 2:
                raise aiohttp.ClientError("Ouch!")

    assert count == 3
    record = ("neuro_sdk.utils", logging.INFO, "Fails: Ouch!.  Retry...")
    assert caplog.record_tuples == [record] * 2


async def test_all_fail(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    with pytest.raises(aiohttp.ClientError):
        for retry in retries("Fails", attempts=3):
            async with retry:
                count += 1
                raise aiohttp.ClientError("Ouch!")

    assert count == 3
    record = ("neuro_sdk.utils", logging.INFO, "Fails: Ouch!.  Retry...")
    assert caplog.record_tuples == [record] * 2


async def test_reset(caplog: Any) -> None:
    caplog.set_level(logging.INFO)
    count = 0
    for retry in retries("Fails", attempts=3):
        async with retry:
            count += 1
            if count in (3, 5):
                retry.reset()
            if count <= 6:
                raise aiohttp.ClientError("Ouch!")

    assert count == 7
    record = ("neuro_sdk.utils", logging.INFO, "Fails: Ouch!.  Retry...")
    assert caplog.record_tuples == [record] * 6


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
