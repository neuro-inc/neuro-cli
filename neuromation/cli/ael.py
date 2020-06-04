# Attach / exec / logs utilities

import asyncio
import codecs
import enum
import functools
import logging
import signal
import sys
import threading
from typing import Any, Awaitable, Callable, Optional

import click
from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import Output, create_output
from prompt_toolkit.shortcuts import PromptSession
from typing_extensions import NoReturn

from neuromation.api import IllegalArgumentError, JobStatus, StdStream

from .const import EX_IOERR, EX_PLATFORMERROR
from .formatters.jobs import ExecStopProgress, JobStopProgress
from .root import Root


log = logging.getLogger(__name__)


JOB_STARTED = click.style(
    "==== Job is running, press Ctrl-C to detach/kill ===", dim=True
)

JOB_STARTED_TTY = click.style(
    "========== Job is running in terminal mode =========", dim=True
)

LOGS_STARTED = click.style(
    "==================== Job's logs ====================", dim=True
)
ATTACH_STARTED = click.style(
    "=================== Job's output ===================", dim=True
)
ATTACH_STARTED_AFTER_LOGS = click.style(
    "======== Job's output, may overlap with logs =======", dim=True
)


class AttachHelper:
    attach_ready: bool
    log_printed: bool
    write_sem: asyncio.Semaphore
    quiet: bool
    skip_stopper: bool

    def __init__(self, *, quiet: bool) -> None:
        self.attach_ready = False
        self.log_printed = False
        self.write_sem = asyncio.Semaphore()
        self.quiet = quiet
        self.skip_stopper = False


async def process_logs(root: Root, job: str, helper: Optional[AttachHelper]) -> None:
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    async for chunk in root.client.jobs.monitor(job):
        if not chunk:
            txt = decoder.decode(b"", final=True)
            if not txt:
                break
        else:
            txt = decoder.decode(chunk)
        if helper is not None:
            if helper.attach_ready:
                return
            async with helper.write_sem:
                if not helper.log_printed and not helper.quiet:
                    click.echo(LOGS_STARTED)
                helper.log_printed = True
                sys.stdout.write(txt)
                sys.stdout.flush()
        else:
            sys.stdout.write(txt)
            sys.stdout.flush()


async def process_exec(root: Root, job: str, cmd: str, tty: bool) -> NoReturn:
    exec_id = await root.client.jobs.exec_create(job, cmd, tty=tty)
    try:
        if tty:
            await _exec_tty(root, job, exec_id)
        else:
            await _exec_non_tty(root, job, exec_id)
    finally:
        root.soft_reset_tty()

    info = await root.client.jobs.exec_inspect(job, exec_id)
    progress = ExecStopProgress.create(tty=root.tty, color=root.color, quiet=root.quiet)
    while info.running:
        await asyncio.sleep(0.2)
        info = await root.client.jobs.exec_inspect(job, exec_id)
        if not progress(info.running):
            sys.exit(EX_IOERR)
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
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                await root.cancel_with_logging(task)


async def _exec_non_tty(root: Root, job: str, exec_id: str) -> None:
    loop = asyncio.get_event_loop()
    helper = AttachHelper(quiet=True)

    async with root.client.jobs.exec_start(job, exec_id) as stream:
        info = await root.client.jobs.exec_inspect(job, exec_id)
        if not info.running:
            sys.exit(info.exit_code)

        tasks = []
        if root.tty:
            tasks.append(loop.create_task(_process_stdin_non_tty(root, stream)))
        tasks.append(loop.create_task(_process_stdout_non_tty(stream, helper)))

        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                await root.cancel_with_logging(task)


async def process_attach(root: Root, job: str, tty: bool, logs: bool) -> NoReturn:
    # Note, the job should be in running/finished state for this call,
    # passing pending job is forbidden
    try:
        if tty:
            await _attach_tty(root, job, logs)
        else:
            skip_stopper = await _attach_non_tty(root, job, logs)
            if skip_stopper:
                sys.exit(128 + signal.SIGINT)
    finally:
        root.soft_reset_tty()

    status = await root.client.jobs.status(job)
    progress = JobStopProgress.create(tty=root.tty, color=root.color, quiet=root.quiet)
    while status.status == JobStatus.RUNNING:
        await asyncio.sleep(0.2)
        status = await root.client.jobs.status(job)
        if not progress(status):
            sys.exit(EX_IOERR)
    if status.status == JobStatus.FAILED:
        sys.exit(status.history.exit_code or EX_PLATFORMERROR)
    sys.exit(status.history.exit_code)


async def _attach_tty(root: Root, job: str, logs: bool) -> None:
    if not root.quiet:
        click.echo(JOB_STARTED_TTY)

    loop = asyncio.get_event_loop()
    helper = AttachHelper(quiet=root.quiet)

    stdout = create_output()
    h, w = stdout.get_size()

    if logs:
        logs_printer = loop.create_task(process_logs(root, job, helper))
    else:
        # Placeholder, prints nothing
        logs_printer = loop.create_task(asyncio.sleep(0))

    async with root.client.jobs.attach(
        job, stdin=True, stdout=True, stderr=True, logs=True
    ) as stream:
        try:
            await root.client.jobs.resize(job, w=w, h=h)
        except IllegalArgumentError:
            # Job may be finished at this moment.
            # Need to check job's status and print logs
            # for finished job
            pass
        status = await root.client.jobs.status(job)
        if status.status is not JobStatus.RUNNING:
            # Job is finished
            await logs_printer
            if status.status == JobStatus.FAILED:
                sys.exit(status.history.exit_code or EX_PLATFORMERROR)
            else:
                sys.exit(status.history.exit_code)

        tasks = []
        tasks.append(loop.create_task(_process_stdin_tty(stream)))
        tasks.append(loop.create_task(_process_stdout_tty(stream, stdout, helper)))
        tasks.append(
            loop.create_task(
                _process_resizing(
                    functools.partial(root.client.jobs.resize, job), stdout
                )
            )
        )
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            print("FINALIZING")
            for task in tasks:
                await root.cancel_with_logging(task)

            await root.cancel_with_logging(logs_printer)
            print("FINALIZED")


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


async def _process_stdout_tty(stream: StdStream, stdout: Output, helper: AttachHelper) -> None:
    codec_info = codecs.lookup("utf8")
    decoder = codec_info.incrementaldecoder("replace")
    while True:
        chunk = await stream.read_out()
        if chunk is None:
            txt = decoder.decode(b"", final=True)
            if not txt:
                return
        else:
            txt = decoder.decode(chunk.data)
        async with helper.write_sem:
            if not helper.quiet and not helper.attach_ready:
                # Print header to stdout only,
                # logs are printed to stdout and never to
                # stderr (but logs printing is stopped by
                # helper.attach_ready = True regardless
                # what stream had receive text in attached mode.
                if helper.log_printed:
                    stdout.write_raw(ATTACH_STARTED_AFTER_LOGS + '\n')
                else:
                    stdout.write_raw(ATTACH_STARTED + '\n')
            helper.attach_ready = True
            stdout.write_raw(txt)
            stdout.flush()


async def _attach_non_tty(root: Root, job: str, logs: bool) -> bool:
    if not root.quiet:
        click.echo(JOB_STARTED)

    loop = asyncio.get_event_loop()
    helper = AttachHelper(quiet=root.quiet)

    if logs:
        logs_printer = loop.create_task(process_logs(root, job, helper))
    else:
        # Placeholder, prints nothing
        logs_printer = loop.create_task(asyncio.sleep(0))

    async with root.client.jobs.attach(
        job, stdin=True, stdout=True, stderr=True, logs=True
    ) as stream:
        status = await root.client.jobs.status(job)
        if status.history.exit_code is not None:
            # Wait for logs printing finish before exit
            await logs_printer
            sys.exit(status.history.exit_code)

        tasks = []
        if root.tty:
            tasks.append(loop.create_task(_process_stdin_non_tty(root, stream)))
        tasks.append(loop.create_task(_process_stdout_non_tty(stream, helper)))
        tasks.append(loop.create_task(_process_ctrl_c(root, job, helper)))

        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            return helper.skip_stopper
        finally:
            for task in tasks:
                await root.cancel_with_logging(task)

            await root.cancel_with_logging(logs_printer)


async def _process_stdin_non_tty(root: Root, stream: StdStream) -> None:
    ev = asyncio.Event()

    def read_ready() -> None:
        ev.set()

    inp = create_input()
    with inp.attach(read_ready):
        while True:
            await ev.wait()
            ev.clear()
            if inp.closed:
                return
            keys = inp.read_keys()  # + inp.flush_keys()
            buf = b"".join(key.data.encode("utf8") for key in keys)
            await stream.write_in(buf)


async def _process_stdout_non_tty(stream: StdStream, helper: AttachHelper) -> None:
    codec_info = codecs.lookup("utf8")
    decoders = {
        1: codec_info.incrementaldecoder("replace"),
        2: codec_info.incrementaldecoder("replace"),
    }
    streams = {1: sys.stdout, 2: sys.stderr}

    async def _write(fileno: int, txt: str) -> None:
        f = streams[fileno]
        async with helper.write_sem:
            if not helper.quiet and not helper.attach_ready:
                # Print header to stdout only,
                # logs are printed to stdout and never to
                # stderr (but logs printing is stopped by
                # helper.attach_ready = True regardless
                # what stream had receive text in attached mode.
                if helper.log_printed:
                    click.echo(ATTACH_STARTED_AFTER_LOGS)
                else:
                    click.echo(ATTACH_STARTED)
            helper.attach_ready = True
            f.write(txt)
            f.flush()

    while True:
        chunk = await stream.read_out()
        if chunk is None:
            for fileno in (1, 2):
                txt = decoders[fileno].decode(b"", final=True)
                if txt:
                    await _write(fileno, txt)
            break
        else:
            txt = decoders[chunk.fileno].decode(chunk.data)
            await _write(chunk.fileno, txt)


class InterruptAction(enum.Enum):
    nothing = enum.auto()
    detach = enum.auto()
    kill = enum.auto()


def _create_interruption_dialog() -> PromptSession[InterruptAction]:
    bindings = KeyBindings()

    @bindings.add(Keys.Enter)
    @bindings.add(Keys.Escape)
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
        "<b>Ctrl-C</b> or <b>C</b> -- Kill\n"
        "<b>Ctrl-D</b> or <b>D</b> -- Detach \n"
        "<b>Enter</b> or <b>ESC</b> -- Continue the attached mode"
    )
    complete_message = merge_formatted_text([message, suffix])
    session: PromptSession[InterruptAction] = PromptSession(
        complete_message, key_bindings=bindings
    )
    return session


async def _process_ctrl_c(root: Root, job: str, helper: AttachHelper) -> None:
    # Exit from _process_ctrl_c() task finishes the outer _attach_non_tty() task
    # Return True if kill/detach was asked.
    # The returned value can be used for skipping the job termination
    queue: asyncio.Queue[Optional[int]] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def on_signal(signum: int, frame: Any) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, signum)

    # Windows even loop has no add_signal_handler() method
    prev_signal = signal.signal(signal.SIGINT, on_signal)

    try:
        while True:
            getter = queue.get()
            if sys.platform == "win32":
                # On Python < 3.8 the interruption handling
                # responds not smoothly because the loop is blocked
                # in proactor for relative long time period.
                # Simple busy loop interrupts the proactor every 100 ms,
                # giving a chance to process other tasks
                getter = asyncio.wait_for(getter, 0.1)
            try:
                signum = await getter
            except asyncio.TimeoutError:
                continue
            if signum is None:
                return
            if not root.tty:
                # Ask nothing but just kill a job
                # if executed from non-terminal
                await root.client.jobs.kill(job)
                helper.skip_stopper = True
                return
            async with helper.write_sem:
                session = _create_interruption_dialog()
                answer = await session.prompt_async(set_exception_handler=False)
                if answer == InterruptAction.detach:
                    click.secho("Detach terminal", dim=True, fg="green")
                    helper.skip_stopper = True
                    return
                elif answer == InterruptAction.kill:
                    click.secho("Kill job", fg="red")
                    await root.client.jobs.kill(job)
                    helper.skip_stopper = True
                    return
    finally:
        signal.signal(signal.SIGINT, prev_signal)
