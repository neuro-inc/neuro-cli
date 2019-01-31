import asyncio
import gc
import sys
import warnings
from typing import Awaitable, TypeVar


_T = TypeVar("_T")


def run(main: Awaitable[_T], *, debug: bool = False) -> _T:
    """Run a coroutine.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop and finalizing asynchronous
    generators.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is True, the event loop will be run in debug mode.

    This function always creates a new event loop and closes it at the end.
    It should be used as a main entry point for asyncio programs, and should
    ideally only be called once.

    Example:

        async def main():
            await asyncio.sleep(1)
            print('hello')

        asyncio.run(main())
    """
    try:
        current_loop = asyncio.get_event_loop()
        if current_loop.is_running():
            raise RuntimeError(
                "asyncio.run() cannot be called from a running event loop"
            )
    except RuntimeError:
        # there is no current loop
        pass

    if not asyncio.iscoroutine(main):
        raise ValueError("a coroutine was expected, got {!r}".format(main))

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(debug)
        main_task = loop.create_task(main)
        return loop.run_until_complete(main_task)
    finally:
        try:
            _cancel_all_tasks(loop, main_task)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            # simple workaround for:
            # http://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                loop.close()
                del loop
                gc.collect(2)


def _cancel_all_tasks(
    loop: asyncio.AbstractEventLoop, main_task: "asyncio.Task[_T]"
) -> None:
    if sys.version_info >= (3, 7):
        to_cancel = asyncio.all_tasks(loop)
    else:
        to_cancel = asyncio.Task.all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True)
    )

    # temporary shut up the logger until aiohttp will be fixed
    # the message scares people :)
    return
    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            if task is main_task:
                continue
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during asyncio.run() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )
