# Distributed tracing support

import os
import types

import aiohttp
from multidict import CIMultiDict


def gen_trace_id() -> str:
    """Return 16 random hexadecimal digits.

    The id is used for distributed tracing.
    """
    return os.urandom(8).hex()


def _update_headers(headers: "CIMultiDict[str]", trace_id: str, span_id: str) -> None:
    """Creates dict with zipkin single header format.
    """
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
    span_id = gen_trace_id()
    _update_headers(params.headers, trace_id, span_id)


def _make_trace_config() -> aiohttp.TraceConfig:
    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(_on_request_start)  # type: ignore
    return trace_config
