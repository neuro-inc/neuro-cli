import asyncio
import gc
import itertools
import logging
import os
import ssl
import sys
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar

from typing_extensions import final

if sys.version_info >= (3, 7):
    from asyncio import current_task
else:
    current_task = asyncio.Task.current_task


_T = TypeVar("_T")
logger = logging.getLogger(__name__)


@final
class Runner:
    def __init__(self, *, debug: bool = False) -> None:
        self._debug = debug
        self._started = False
        self._stopped = False
        self._executor = ThreadPoolExecutor()
        self._loop = asyncio.new_event_loop()
        self._loop.set_default_executor(self._executor)
        _setup_exception_handler(self._loop, self._debug)

    def run(self, main: Awaitable[_T]) -> _T:
        assert self._started
        assert not self._stopped
        if not asyncio.iscoroutine(main):
            raise ValueError(f"a coroutine was expected, got {main!r}")
        main_task = self._loop.create_task(main)

        if sys.version_info <= (3, 7):

            def retrieve_exc(fut: "asyncio.Task[Any]") -> None:
                # suppress exception printing
                if not fut.cancelled():
                    fut.exception()

            main_task.add_done_callback(retrieve_exc)

        return self._loop.run_until_complete(main_task)

    def __enter__(self) -> "Runner":
        assert not self._started
        assert not self._stopped
        self._started = True

        try:
            current_loop = asyncio.get_event_loop()
        except RuntimeError:
            # there is no current loop
            pass
        else:
            if current_loop.is_running():
                raise RuntimeError(
                    "asyncio.run() cannot be called from a running event loop"
                )

        asyncio.set_event_loop(self._loop)
        self._loop.set_debug(self._debug)
        return self

    def __exit__(
        self, exc_type: Type[BaseException], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        assert self._started
        assert not self._stopped
        try:
            _cancel_all_tasks(self._loop)
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        finally:
            self._executor.shutdown(wait=True)
            asyncio.set_event_loop(None)
            # simple workaround for:
            # http://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                self._loop.close()
                del self._loop
                gc.collect()


def run(main: Awaitable[_T], *, debug: bool = False) -> _T:
    # Backport from python 3.7

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
    with Runner(debug=debug) as runner:
        return runner.run(main)


def _exception_handler(
    loop: asyncio.AbstractEventLoop, context: Dict[str, Any]
) -> None:
    if context.get("message") in {
        "SSL error in data received",
        "Fatal error on transport",
    }:
        # validate we have the right exception, transport and protocol
        exception = context.get("exception")
        if isinstance(exception, ssl.SSLError) and exception.reason == "KRB5_S_INIT":
            return

    loop.default_exception_handler(context)


def _setup_exception_handler(loop: asyncio.AbstractEventLoop, debug: bool) -> None:
    if debug:
        return
    loop.set_exception_handler(_exception_handler)


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    if sys.version_info >= (3, 7):
        to_cancel = asyncio.all_tasks(loop)
    else:
        to_cancel = [t for t in asyncio.Task.all_tasks(loop) if not t.done()]
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
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during asyncio.run() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


if sys.platform != "win32":
    from asyncio.unix_events import AbstractChildWatcher

    _Callback = Callable[..., None]

    class ThreadedChildWatcher(AbstractChildWatcher):
        # Backport from Python 3.8

        """Threaded child watcher implementation.

        The watcher uses a thread per process
        for waiting for the process finish.

        It doesn't require subscription on POSIX signal
        but a thread creation is not free.

        The watcher has O(1) complexity, its performance doesn't depend
        on amount of spawn processes.
        """

        def __init__(self) -> None:
            self._pid_counter = itertools.count(0)
            self._threads: Dict[int, threading.Thread] = {}

        def close(self) -> None:
            pass

        def __enter__(self) -> "ThreadedChildWatcher":
            return self

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> None:
            pass

        def __del__(self, _warn: Any = warnings.warn) -> None:
            threads = [
                thread for thread in list(self._threads.values()) if thread.is_alive()
            ]
            if threads:
                _warn(
                    f"{self.__class__} has registered but not finished child processes",
                    ResourceWarning,
                    source=self,
                )

        def add_child_handler(self, pid: int, callback: _Callback, *args: Any) -> None:
            loop = asyncio.get_event_loop()
            thread = threading.Thread(
                target=self._do_waitpid,
                name=f"waitpid-{next(self._pid_counter)}",
                args=(loop, pid, callback, args),
                daemon=True,
            )
            self._threads[pid] = thread
            thread.start()

        def remove_child_handler(self, pid: int) -> bool:
            # asyncio never calls remove_child_handler() !!!
            # The method is no-op but is implemented because
            # abstract base classe requires it
            return True

        def attach_loop(self, loop: Optional[asyncio.AbstractEventLoop]) -> None:
            pass

        def _do_waitpid(
            self,
            loop: asyncio.AbstractEventLoop,
            expected_pid: int,
            callback: _Callback,
            args: List[Any],
        ) -> None:
            assert expected_pid > 0

            try:
                pid, status = os.waitpid(expected_pid, 0)
            except ChildProcessError:
                # The child process is already reaped
                # (may happen if waitpid() is called elsewhere).
                pid = expected_pid
                returncode = 255
                logger.warning(
                    "Unknown child process pid %d, will report returncode 255", pid
                )
            else:
                returncode = _compute_returncode(status)
                if loop.get_debug():
                    logger.debug(
                        "process %s exited with returncode %s", expected_pid, returncode
                    )

            if loop.is_closed():
                logger.warning("Loop %r that handles pid %r is closed", loop, pid)
            else:
                loop.call_soon_threadsafe(callback, pid, returncode, *args)

            self._threads.pop(expected_pid)

    def _compute_returncode(status: int) -> int:
        if os.WIFSIGNALED(status):
            # The child process died because of a signal.
            return -os.WTERMSIG(status)
        elif os.WIFEXITED(status):
            # The child process exited (e.g sys.exit()).
            return os.WEXITSTATUS(status)
        else:
            # The child exited, but we don't understand its status.
            # This shouldn't happen, but if it does, let's just
            # return that status; perhaps that helps debug it.
            return status


def setup_child_watcher() -> None:
    if sys.platform == "win32":
        if sys.version_info < (3, 7):
            # Python 3.6 has no WindowsProactorEventLoopPolicy class
            from asyncio import events

            class WindowsProactorEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
                _loop_factory = asyncio.ProactorEventLoop

        else:
            WindowsProactorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    else:
        if sys.version_info < (3, 8):
            asyncio.set_child_watcher(ThreadedChildWatcher())
