# Distributed tracing support

import os
import random
import time
import types

import aiohttp
from multidict import CIMultiDict


def gen_trace_id() -> str:
    """Return 32 random hexadecimal digits.

    The upper 32 bits are the current time in epoch seconds, and the
    lower 96 bits are random. This allows for AWS X-Ray `interop
    <https://github.com/openzipkin/zipkin/issues/1754>`_

    The id is used for distributed tracing.
    """

    high = int(time.time())
    low = random.getrandbits(96)
    return "{:032x}".format((high << 96) | low)


def _gen_span_id() -> str:
    """Return 16 random hexadecimal digits.

    The id is used for distributed tracing.
    """
    return os.urandom(8).hex()


def _update_headers(headers: "CIMultiDict[str]", trace_id: str, span_id: str) -> None:
    """Creates dict with zipkin single header format."""
    # b3={TraceId}-{SpanId}-{SamplingState}-{ParentSpanId}
    headers["b3"] = f"{trace_id}-{span_id}"


async def _on_request_start(
    session: aiohttp.ClientSession,
    context: types.SimpleNamespace,
    params: aiohttp.TraceRequestStartParams,
) -> None:
    trace_ctx = context.trace_request_ctx
    trace_id = getattr(trace_ctx, "trace_id", None)
    if trace_id is None:
        return
    span_id = _gen_span_id()
    _update_headers(params.headers, trace_id, span_id)


def _make_trace_config() -> aiohttp.TraceConfig:
    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(_on_request_start)  # type: ignore
    return trace_config
