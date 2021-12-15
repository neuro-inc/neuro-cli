import asyncio
import functools
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
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from typing_extensions import final

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)

logger = logging.getLogger(__name__)


@final
class Runner:
    def __init__(self, *, debug: bool = False) -> None:
        self._debug = debug
        self._started = False
        self._stopped = False
        self._executor = ThreadPoolExecutor()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def run(self, main: Awaitable[_T]) -> _T:
        assert self._started
        assert not self._stopped
        assert self._loop is not None
        if not asyncio.iscoroutine(main):
            raise ValueError(f"a coroutine was expected, got {main!r}")
        main_task = self._loop.create_task(main)

        return self._loop.run_until_complete(main_task)

    def __enter__(self) -> "Runner":
        assert not self._started
        assert not self._stopped
        self._started = True
        assert self._loop is None
        self._loop = asyncio.new_event_loop()
        self._loop.set_default_executor(self._executor)
        self._loop.set_debug(self._debug)
        if not self._debug:
            self._loop.set_exception_handler(_exception_handler)
        return self

    def __exit__(
        self, exc_type: Type[BaseException], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        assert self._started, "Loop was not started"
        assert self._loop is not None
        if self._stopped:
            return
        if self._loop.is_closed():
            return
        try:
            _cancel_all_tasks(self._loop)
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        finally:
            # simple workaround for:
            # http://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                self._loop.close()
                del self._loop
                gc.collect()
            self._executor.shutdown(wait=True)
        self._stopped = True


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


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    to_cancel = asyncio.all_tasks(loop)

    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))

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
        WindowsProactorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    else:
        if sys.version_info < (3, 8):
            asyncio.set_child_watcher(ThreadedChildWatcher())


# TODO (S Storchaka 2021-06-01): Methods __aiter__ and __anext__
# are supported for compatibility, but using the iterator without
# "async with" is strongly discouraged. In future these methods
# will be deprecated and finally removed. It will be just a context
# manager returning an iterator.
class _AsyncIteratorAndContextManager(
    Generic[_T_co],
    AsyncIterator[_T_co],
    AsyncContextManager[AsyncIterator[_T_co]],
):
    def __init__(self, gen: AsyncIterator[_T_co]) -> None:
        self._gen = gen

    async def __aenter__(self) -> AsyncIterator[_T_co]:
        return self._gen

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        # Actually it is an AsyncGenerator.
        await self._gen.aclose()  # type: ignore

    def __aiter__(self) -> AsyncIterator[_T_co]:
        return self._gen.__aiter__()

    def __anext__(self) -> Awaitable[_T_co]:
        return self._gen.__anext__()


# XXX (S Storchaka 2021-06-01): The decorated function should actually
# return an AsyncGenerator, but all of our generator functions are annotated
# as returning an AsyncIterator.
def asyncgeneratorcontextmanager(
    func: Callable[..., AsyncIterator[_T_co]]
) -> Callable[..., _AsyncIteratorAndContextManager[_T_co]]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> _AsyncIteratorAndContextManager[_T_co]:
        gen = func(*args, **kwargs)
        return _AsyncIteratorAndContextManager[_T_co](gen)

    return wrapper
