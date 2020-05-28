# Attach / exec / logs utilities

import asyncio
import codecs
import contextlib
import dataclasses
import enum
import functools
import logging
import signal
import sys
import threading
from typing import Any, AsyncIterator, Awaitable, Callable, Optional

import async_timeout
import click
from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import Output, create_output
from prompt_toolkit.shortcuts import PromptSession

from neuromation.api import IllegalArgumentError, JobStatus, StdStream
from neuromation.api.utils import asynccontextmanager

from .asyncio_utils import current_task
from .const import EX_IOERR, EX_PLATFORMERROR
from .formatters.jobs import JobStopProgress
from .root import Root


log = logging.getLogger(__name__)

LOGS_STARTED = click.style(
    "==================== job's logs ====================\n", dim=True
)
ATTACH_STARTED = click.style(
    "=================== job's output ===================\n", dim=True
)
ATTACH_STARTED_AFTER_LOGS = click.style(
    "======== job's output, may overlap with logs =======\n", dim=True
)


@dataclasses.dataclass(frozen=True)
class AttachHelper:
    attach_ready: asyncio.Event
    log_printed: asyncio.Event
    write_sem: asyncio.Semaphore


async def process_logs(root: Root, job: str, helper: Optional[AttachHelper]) -> None:
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    async for chunk in root.client.jobs.monitor(job):
        if not chunk:
            break
        txt = decoder.decode(chunk)
        if helper is not None:
            if helper.attach_ready.is_set():
                return
            async with helper.write_sem:
                if not helper.log_printed.is_set() and not root.quiet:
                    click.echo(LOGS_STARTED, nl=False)
                helper.log_printed.set()
                click.echo(txt, nl=False)
        else:
            click.echo(txt, nl=False)


async def process_exec(root: Root, job: str, cmd: str, tty: bool) -> None:
    exec_id = await root.client.jobs.exec_create(job, cmd, tty=tty)
    if tty:
        await _exec_tty(root, job, exec_id)
    else:
        await _exec_non_tty(root, job, exec_id)

    info = await root.client.jobs.exec_inspect(job, exec_id)
    while info.running:
        await asyncio.sleep(0.1)
        info = await root.client.jobs.exec_inspect(job, exec_id)
    sys.exit(info.exit_code)


async def _exec_tty(root: Root, job: str, exec_id: str) -> None:
    loop = asyncio.get_event_loop()
    stdout = create_output()
    h, w = stdout.get_size()
    async with root.client.jobs.exec_start(job, exec_id) as stream:
        try:
            await root.client.jobs.exec_resize(job, exec_id, w=w, h=h)
        except IllegalArgumentError:
            info = await root.client.jobs.exec_inspect(job, exec_id)
            if not info.running:
                # Exec session is finished
                return

        tasks = []
        tasks.append(loop.create_task(_process_stdin_tty(stream)))
        tasks.append(loop.create_task(_process_stdout_tty(stream, stdout)))
        tasks.append(
            loop.create_task(
                _process_resizing(
                    functools.partial(root.client.jobs.exec_resize, job, exec_id),
                    stdout,
                )
            )
        )
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in tasks:
            await root.cancel_with_logging(task)


async def _exec_non_tty(root: Root, job: str, exec_id: str) -> None:
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    async with root.client.jobs.exec_start(job, exec_id) as stream:
        info = await root.client.jobs.exec_inspect(job, exec_id)
        if not info.running:
            raise sys.exit(info.exit_code)
        while True:
            chunk = await stream.read_out()
            if chunk is None:
                break
            if chunk.stream == 2:
                f = sys.stderr
            else:
                f = sys.stdout
            txt = decoder.decode(chunk.data)
            if txt is not None:
                f.write(txt)
                f.flush()


async def process_attach(root: Root, job: str, tty: bool, logs: bool) -> None:
    try:
        # Note, the job should be in running/finished state for this call,
        # passing pending job is forbidden
        if tty:
            # docker doesn't proxy signals for non-tty
            await _attach_tty(root, job, logs)
        else:
            await _attach_non_tty(root, job, logs)

        status = await root.client.jobs.status(job)
        progress = JobStopProgress.create(
            tty=root.tty, color=root.color, quiet=root.quiet
        )
        while status.status == JobStatus.RUNNING:
            await asyncio.sleep(0.2)
            status = await root.client.jobs.status(job)
            if not progress(status):
                sys.exit(EX_IOERR)
        if status.status == JobStatus.FAILED:
            sys.exit(status.history.exit_code or EX_PLATFORMERROR)
        sys.exit(status.history.exit_code)
    except asyncio.CancelledError:
        # Note: Cancellation is a normal shutdown,
        # there is no need to report user about this fact
        sys.exit(1)


async def _attach_tty(root: Root, job: str, logs: bool) -> None:
    loop = asyncio.get_event_loop()
    stdout = create_output()
    h, w = stdout.get_size()
    async with root.client.jobs.attach(
        job, stdin=True, stdout=True, stderr=True, logs=True
    ) as stream:
        try:
            await root.client.jobs.resize(job, w=w, h=h)
        except IllegalArgumentError:
            status = await root.client.jobs.status(job)
            if status.status is not JobStatus.RUNNING:
                # Job is finished
                return

        tasks = []
        tasks.append(loop.create_task(_process_stdin_tty(stream)))
        tasks.append(loop.create_task(_process_stdout_tty(stream, stdout)))
        tasks.append(
            loop.create_task(
                _process_resizing(
                    functools.partial(root.client.jobs.resize, job), stdout
                )
            )
        )
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in tasks:
            await root.cancel_with_logging(task)


async def _process_resizing(
    resizer: Callable[..., Awaitable[None]], stdout: Output
) -> None:
    loop = asyncio.get_event_loop()
    resize_event = asyncio.Event()

    def resize() -> None:
        resize_event.set()

    has_sigwinch = (
        hasattr(signal, "SIGWINCH")
        and threading.current_thread() is threading.main_thread()
    )
    if has_sigwinch:
        previous_winch_handler = signal.getsignal(signal.SIGWINCH)
        loop.add_signal_handler(signal.SIGWINCH, resize)
        if previous_winch_handler is None:
            # Borrowed from the Prompt Toolkit.
            # In some situations we receive `None`. This is
            # however not a valid value for passing to
            # `signal.signal` at the end of this block.
            previous_winch_handler = signal.SIG_DFL

    prevh = prevw = None
    try:
        while True:
            if has_sigwinch:
                await resize_event.wait()
                resize_event.clear()
            else:
                # Windows or non-main thread
                # The logic is borrowed from docker CLI.
                # Wait for 250 ms
                # If there is no resize event -- check the size anyway on timeout.
                # It makes resizing to work on Windows.
                await asyncio.sleep(0.25)
            h, w = stdout.get_size()
            if prevh != h or prevw != w:
                prevh = h
                prevw = w
                await resizer(w=w, h=h)
    finally:
        if has_sigwinch:
            loop.remove_signal_handler(signal.SIGWINCH)
            signal.signal(signal.SIGWINCH, previous_winch_handler)


async def _process_stdin_tty(stream: StdStream) -> None:
    ev = asyncio.Event()

    def read_ready() -> None:
        ev.set()

    inp = create_input()
    with inp.raw_mode():
        with inp.attach(read_ready):
            while True:
                await ev.wait()
                ev.clear()
                if inp.closed:
                    return
                keys = inp.read_keys()  # + inp.flush_keys()
                buf = b"".join(key.data.encode("utf8") for key in keys)
                await stream.write_in(buf)


async def _process_stdout_tty(stream: StdStream, stdout: Output) -> None:
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    while True:
        chunk = await stream.read_out()
        if chunk is None:
            return
        txt = decoder.decode(chunk.data)
        if txt is not None:
            stdout.write_raw(txt)
            stdout.flush()


async def _attach_non_tty(root: Root, job: str, logs: bool) -> None:
    if not root.quiet:
        click.secho("Job is running, press Ctrl-C to detach/kill.", dim=True)
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    async with _handle_ctrl_c(root, job) as write_sem:
        async with _print_logs_until_attached(root, job, logs, write_sem) as helper:
            async with root.client.jobs.attach(
                job, stdin=False, stdout=True, stderr=True, logs=True
            ) as stream:
                status = await root.client.jobs.status(job)
                if status.history.exit_code is not None:
                    raise sys.exit(status.history.exit_code)
                while True:
                    chunk = await stream.read_out()
                    if chunk is None:
                        break
                    if chunk.stream == 2:
                        f = sys.stderr
                    else:
                        f = sys.stdout
                    txt = decoder.decode(chunk.data)
                    async with write_sem:
                        if txt is not None:
                            if not root.quiet and not helper.attach_ready.is_set():
                                if helper.log_printed.is_set():
                                    click.echo(ATTACH_STARTED_AFTER_LOGS, nl=False)
                                else:
                                    click.echo(ATTACH_STARTED, nl=False)
                            helper.attach_ready.set()
                            f.write(txt)
                            f.flush()


@asynccontextmanager
async def _print_logs_until_attached(
    root: Root, job: str, logs: bool, write_sem: asyncio.Semaphore
) -> AsyncIterator[AttachHelper]:
    attach_ready = asyncio.Event()
    logs_printed = asyncio.Event()
    helper = AttachHelper(attach_ready, logs_printed, write_sem)
    if not logs:
        yield helper
        return

    loop = asyncio.get_event_loop()
    reader = loop.create_task(process_logs(root, job, helper))

    async def wait_attached() -> None:
        await attach_ready.wait()
        # Job is attached, stop logs reading
        await root.cancel_with_logging(reader)

    waiter = loop.create_task(wait_attached())

    try:
        yield helper
    finally:
        await root.cancel_with_logging(waiter)
        if not attach_ready.is_set():
            # Job is finished before actuall attaching,
            # read all collected logs
            await reader
        else:
            # Cancel logs reader just in case
            await root.cancel_with_logging(reader)


class InterruptAction(enum.Enum):
    nothing = enum.auto()
    detach = enum.auto()
    kill = enum.auto()


def _create_interruption_dialog() -> PromptSession[InterruptAction]:
    bindings = KeyBindings()

    @bindings.add(Keys.Enter)
    def nothing(event: KeyPressEvent) -> None:
        event.app.exit(result=InterruptAction.nothing)

    @bindings.add("c-c")
    @bindings.add("C")
    @bindings.add("c")
    def kill(event: KeyPressEvent) -> None:
        event.app.exit(result=InterruptAction.kill)

    @bindings.add("c-d")
    @bindings.add("D")
    @bindings.add("d")
    def detach(event: KeyPressEvent) -> None:
        event.app.exit(result=InterruptAction.detach)

    @bindings.add(Keys.Any)
    def _(event: KeyPressEvent) -> None:
        # Disallow inserting other text.
        pass

    message = HTML("  <b>Interrupted</b>. Please choose the action:\n")
    suffix = HTML(
        "<b>Ctrl-C</b> or <b>C</b> (kill), "
        "<b>Ctrl-D</b> or <b>D</b> (detach), "
        "<b>Enter</b> (continue the attached mode)"
    )
    complete_message = merge_formatted_text([message, suffix])
    session: PromptSession[InterruptAction] = PromptSession(
        complete_message, key_bindings=bindings
    )
    return session


async def _process_interruption(
    root: Root,
    job: str,
    queue: "asyncio.Queue[Optional[int]]",
    write_sem: asyncio.Semaphore,
    main_task: "asyncio.Task[None]",
) -> None:
    try:
        while True:
            signum = await queue.get()
            if signum is None:
                return
            async with write_sem:
                session = _create_interruption_dialog()
                answer = await session.prompt_async()
                if answer == InterruptAction.detach:
                    click.secho("Detach terminal", dim=True, fg="green")
                    main_task.cancel()
                elif answer == InterruptAction.kill:
                    click.secho("Kill job", fg="red")
                    await root.client.jobs.kill(job)
                    main_task.cancel()
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        if root.show_traceback:
            log.exception(str(exc), stack_info=True)
        else:
            log.error(str(exc))
        main_task.cancel()


@asynccontextmanager
async def _handle_ctrl_c(root: Root, job: str) -> AsyncIterator[asyncio.Semaphore]:
    queue: asyncio.Queue[Optional[int]] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    write_sem = asyncio.Semaphore()

    def on_signal(signum: int, frame: Any) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, signum)

    signal.signal(signal.SIGINT, on_signal)

    task = loop.create_task(
        _process_interruption(root, job, queue, write_sem, current_task())
    )

    async def busy_loop() -> None:
        # On Python < 3.8 the interruption handling
        # responses not smoothly because the loop is blocked
        # in proactor for relative long time period.
        # Simple busy loop interrupts the proactor every 100 ms,
        # giving a chance to process other tasks
        # UNIX doesn't need this hack.
        if sys.platform != "win32":
            return
        while True:
            await asyncio.sleep(0.1)

    busy_task = loop.create_task(busy_loop())

    yield write_sem

    signal.signal(signal.SIGINT, signal.default_int_handler)

    await queue.put(None)
    await task

    await root.cancel_with_logging(busy_task)
