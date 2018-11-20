from unittest.mock import MagicMock

import pytest

from neuromation.http.fetch import SyncStreamWrapper


@pytest.mark.asyncio
async def test_stream_reading(loop):
    initial_buf_values = bytearray(range(100, 0, -1))
    values_read_from_stream = bytearray(range(len(initial_buf_values)))

    async def read_op(arr_length):
        return bytearray(range(arr_length))

    underlying_stream = MagicMock()
    underlying_stream.read = read_op

    wrapper = SyncStreamWrapper(None, loop=loop)
    wrapper._stream_reader = underlying_stream

    my_buf = initial_buf_values
    await wrapper.readinto(my_buf)

    assert my_buf == values_read_from_stream
