import asyncio
import contextlib
import logging
import re
import shlex
import sys
import uuid
import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Set, Tuple

import async_timeout
import click
from dateutil.parser import isoparse
from yarl import URL

from neuromation.api import (
    AuthorizationError,
    Client,
    Container,
    HTTPPort,
    JobDescription,
    JobRestartPolicy,
    JobStatus,
    RemoteImage,
    Resources,
    Volume,
)
from neuromation.cli.formatters.images import DockerImageProgress
from neuromation.cli.formatters.utils import (
    URIFormatter,
    image_formatter,
    uri_formatter,
)

from .ael import process_attach, process_exec, process_logs
from .click_types import (
    JOB,
    JOB_COLUMNS,
    JOB_NAME,
    LOCAL_REMOTE_PORT,
    MEGABYTE,
    PRESET,
    ImageType,
)
from .const import EX_PLATFORMERROR
from .defaults import (
    GPU_MODELS,
    JOB_CPU_NUMBER,
    JOB_GPU_MODEL,
    JOB_GPU_NUMBER,
    JOB_MEMORY_AMOUNT,
)
from .formatters.jobs import (
    BaseJobsFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    SimpleJobsFormatter,
    TabularJobsFormatter,
)
from .parse_utils import JobColumnInfo, get_default_columns, parse_columns
from .root import Root
from .utils import (
    NEURO_STEAL_CONFIG,
    AsyncExitStack,
    alias,
    argument,
    command,
    deprecated_quiet_option,
    group,
    option,
    pager_maybe,
    resolve_job,
    volume_to_verbose_str,
)


log = logging.getLogger(__name__)

STORAGE_MOUNTPOINT = "/var/storage"

DEFAULT_JOB_LIFE_SPAN = "1d"
REGEX_TIME_DELTA = re.compile(
    r"^((?P<d>\d+)d)?((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s)?$"
)


TTY_OPT = option(
    "-t/-T",
    "--tty/--no-tty",
    is_flag=True,
    default=None,
    help=(
        "Allocate a TTY, can be useful for interactive jobs. "
        "By default is on if the command is executed from a terminal, "
        "non-tty mode is used if executed from a script."
    ),
)


@group()
def job() -> None:
    """
    Job operations.
    """


@command(
    context_settings=dict(allow_interspersed_args=False), hidden=True, deprecated=True
)
@argument("image", type=ImageType())
@argument("cmd", nargs=-1, type=click.UNPROCESSED)
@option(
    "-g",
    "--gpu",
    metavar="NUMBER",
    type=int,
    help="Number of GPUs to request",
    default=JOB_GPU_NUMBER,
    show_default=True,
)
@option(
    "--gpu-model",
    metavar="MODEL",
    type=click.Choice(GPU_MODELS),
    help="GPU to use",
    default=JOB_GPU_MODEL,
    show_default=True,
)
@option("--tpu-type", metavar="TYPE", type=str, help="TPU type to use")
@option(
    "tpu_software_version",
    "--tpu-sw-version",
    metavar="VERSION",
    type=str,
    help="Requested TPU software version",
)
@option(
    "-c",
    "--cpu",
    metavar="NUMBER",
    type=float,
    help="Number of CPUs to request",
    default=JOB_CPU_NUMBER,
    show_default=True,
)
@option(
    "-m",
    "--memory",
    metavar="AMOUNT",
    type=MEGABYTE,
    help="Memory amount to request",
    default=JOB_MEMORY_AMOUNT,
    show_default=True,
)
@option(
    "-x/-X",
    "--extshm/--no-extshm",
    is_flag=True,
    default=True,
    show_default=True,
    help="Request extended '/dev/shm' space",
)
@option("--http", type=int, metavar="PORT", help="Enable HTTP port forwarding to a job")
@option(
    "--http-auth/--no-http-auth",
    is_flag=True,
    help="Enable HTTP authentication for forwarded HTTP port  [default: True]",
    default=None,
)
@option(
    "--preemptible/--non-preemptible",
    "-p/-P",
    help="Run job on a lower-cost preemptible instance",
    default=False,
    show_default=True,
)
@option(
    "-n",
    "--name",
    metavar="NAME",
    type=JOB_NAME,
    help="Optional job name",
    default=None,
    secure=True,
)
@option(
    "--tag",
    metavar="TAG",
    type=str,
    help="Optional job tag, multiple values allowed",
    multiple=True,
)
@option(
    "-d",
    "--description",
    metavar="DESC",
    help="Optional job description in free format",
    secure=True,
)
@deprecated_quiet_option
@option(
    "-v",
    "--volume",
    metavar="MOUNT",
    multiple=True,
    help=(
        "Mounts directory from vault into container. "
        "Use multiple options to mount more than one volume. "
        "Use --volume=ALL to mount all accessible storage directories."
    ),
    secure=True,
)
@option(
    "--entrypoint",
    type=str,
    help=(
        "Executable entrypoint in the container "
        "(note that it overwrites `ENTRYPOINT` and `CMD` "
        "instructions of the docker image)"
    ),
    secure=True,
)
@option(
    "-e",
    "--env",
    metavar="VAR=VAL",
    multiple=True,
    help=(
        "Set environment variable in container "
        "Use multiple options to define more than one variable"
    ),
    secure=True,
)
@option(
    "--env-file",
    type=click.Path(exists=True),
    multiple=True,
    help="File with environment variables to pass",
    secure=True,
)
@option(
    "--restart",
    default="never",
    show_default=True,
    type=click.Choice([str(i) for i in JobRestartPolicy]),
    help="Restart policy to apply when a job exits",
)
@option(
    "--life-span",
    type=str,
    metavar="TIMEDELTA",
    help=(
        "Optional job run-time limit in the format '1d2h3m4s' "
        "(some parts may be missing). Set '0' to disable. "
        "Default value '1d' can be changed in the user config."
    ),
)
@option(
    "--wait-start/--no-wait-start",
    default=True,
    show_default=True,
    help="Wait for a job start or failure",
)
@option(
    "--pass-config/--no-pass-config",
    default=False,
    show_default=True,
    help="Upload neuro config to the job",
)
@option(
    "--port-forward",
    type=LOCAL_REMOTE_PORT,
    multiple=True,
    metavar="LOCAL_PORT:REMOTE_RORT",
    help="Forward port(s) of a running job to local port(s) "
    "(use multiple times for forwarding several ports)",
)
@option("--browse", is_flag=True, help="Open a job's URL in a web browser")
@option(
    "--detach",
    is_flag=True,
    help="Don't attach to job logs and don't wait for exit code",
)
@TTY_OPT
async def submit(
    root: Root,
    image: RemoteImage,
    gpu: Optional[int],
    gpu_model: Optional[str],
    tpu_type: Optional[str],
    tpu_software_version: Optional[str],
    cpu: float,
    memory: int,
    extshm: bool,
    http: Optional[int],
    http_auth: Optional[bool],
    entrypoint: Optional[str],
    cmd: Sequence[str],
    working_dir: Optional[str],
    volume: Sequence[str],
    env: Sequence[str],
    env_file: Sequence[str],
    restart: str,
    life_span: Optional[str],
    port_forward: List[Tuple[int, int]],
    preemptible: bool,
    name: Optional[str],
    tag: Sequence[str],
    description: Optional[str],
    wait_start: bool,
    pass_config: bool,
    browse: bool,
    detach: bool,
    tty: Optional[bool],
) -> None:
    """
    Submit an image to run on the cluster.

    IMAGE container image name.

    CMD list will be passed as commands to model container.

    Examples:

    # Starts a container pytorch:latest with two paths mounted. Directory /q1/
    # is mounted in read only mode to /qm directory within container.
    # Directory /mod mounted to /mod directory in read-write mode.
    neuro submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw \
      pytorch:latest

    # Starts a container using the custom image my-ubuntu:latest stored in neuromation
    # registry, run /script.sh and pass arg1 arg2 arg3 as its arguments:
    neuro submit image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2 arg3
    """
    if tty is None:
        tty = root.tty
    await run_job(
        root,
        image=image,
        gpu=gpu,
        gpu_model=gpu_model,
        tpu_type=tpu_type,
        tpu_software_version=tpu_software_version,
        cpu=cpu,
        memory=memory,
        extshm=extshm,
        http=http,
        http_auth=http_auth,
        entrypoint=entrypoint,
        cmd=cmd,
        working_dir=working_dir,
        volume=volume,
        env=env,
        env_file=env_file,
        restart=restart,
        life_span=life_span,
        port_forward=port_forward,
        preemptible=preemptible,
        name=name,
        tags=tag,
        description=description,
        wait_start=wait_start,
        pass_config=pass_config,
        browse=browse,
        detach=detach,
        tty=tty,
        schedule_timeout=None,
    )


@command(context_settings=dict(allow_interspersed_args=False))
@argument("job", type=JOB)
@argument("cmd", nargs=-1, type=click.UNPROCESSED, required=True)
@TTY_OPT
@option(
    "--no-key-check",
    is_flag=True,
    help="Disable host key checks. Should be used with caution.",
    hidden=True,
)
@option(
    "--timeout",
    default=0,
    type=float,
    show_default=True,
    hidden=True,
    help="Maximum allowed time for executing the command, 0 for no timeout",
)
async def exec(
    root: Root,
    job: str,
    tty: Optional[bool],
    no_key_check: bool,
    cmd: Sequence[str],
    timeout: float,
) -> None:
    """
    Execute command in a running job.

    Examples:

    # Provides a shell to the container:
    neuro exec my-job /bin/bash

    # Executes a single command in the container and returns the control:
    neuro exec --no-tty my-job ls -l
    """
    real_cmd = _parse_cmd(cmd)
    job = await resolve_job(
        job, client=root.client, status={JobStatus.PENDING, JobStatus.RUNNING}
    )
    if tty is None:
        tty = root.tty
    _check_tty(root, tty)
    await process_exec(root, job, real_cmd, tty)


@command()
@argument("job", type=JOB)
@argument(
    "local_remote_port",
    type=LOCAL_REMOTE_PORT,
    nargs=-1,
    required=True,
    metavar="LOCAL_PORT:REMOTE_RORT...",
)
@option(
    "--no-key-check",
    is_flag=True,
    help="Disable host key checks. Should be used with caution.",
    hidden=True,
)
async def port_forward(
    root: Root, job: str, no_key_check: bool, local_remote_port: List[Tuple[int, int]]
) -> None:
    """
    Forward port(s) of a running job to local port(s).

    Examples:

    # Forward local port 2080 to port 80 of job's container.
    # You can use http://localhost:2080 in browser to access job's served http
    neuro job port-forward my-fastai-job 2080:80

    # Forward local port 2222 to job's port 22
    # Then copy all data from container's folder '/data' to current folder
    # (please run second command in other terminal)
    neuro job port-forward my-job-with-ssh-server 2222:22
    rsync -avxzhe "ssh -p 2222" root@localhost:/data .

    # Forward few ports at once
    neuro job port-forward my-job 2080:80 2222:22 2000:100

    """
    if no_key_check:
        click.secho(
            "--no-key-check option is deprecated and "
            "will be removed from the future Neuro CLI release",
            fg="red",
            err=True,
        )
    job_id = await resolve_job(
        job, client=root.client, status={JobStatus.PENDING, JobStatus.RUNNING}
    )
    async with AsyncExitStack() as stack:
        for local_port, job_port in local_remote_port:
            click.echo(
                f"Port localhost:{local_port} will be forwarded "
                f"to port {job_port} of {job_id}"
            )
            await stack.enter_async_context(
                root.client.jobs.port_forward(job_id, local_port, job_port)
            )

        click.echo("Press ^C to stop forwarding")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass


@command()
@argument("job", type=JOB)
async def logs(root: Root, job: str) -> None:
    """
    Print the logs for a job.
    """
    id = await resolve_job(
        job,
        client=root.client,
        status={
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
            JobStatus.FAILED,
        },
    )
    await process_logs(root, id, None)


@command()
@argument("job", type=JOB)
@option(
    "--port-forward",
    type=LOCAL_REMOTE_PORT,
    multiple=True,
    metavar="LOCAL_PORT:REMOTE_RORT",
    help="Forward port(s) of a running job to local port(s) "
    "(use multiple times for forwarding several ports)",
)
async def attach(root: Root, job: str, port_forward: List[Tuple[int, int]]) -> None:
    """
    Attach local standard input, output, and error streams to a running job.
    """
    id = await resolve_job(
        job,
        client=root.client,
        status={
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
            JobStatus.FAILED,
        },
    )
    status = await root.client.jobs.status(id)
    progress = JobStartProgress.create(tty=root.tty, color=root.color, quiet=root.quiet)
    while status.status == JobStatus.PENDING:
        await asyncio.sleep(0.2)
        status = await root.client.jobs.status(id)
        progress.step(status)
    tty = status.container.tty
    _check_tty(root, tty)

    await process_attach(root, status, tty=tty, logs=False, port_forward=port_forward)


@command()
@option(
    "-s",
    "--status",
    multiple=True,
    type=click.Choice(["pending", "running", "succeeded", "failed", "all"]),
    help=(
        "Filter out jobs by status (multiple option)."
        " Note: option `all` is deprecated, use `neuro ps -a` instead."
    ),
)
@option(
    "-o",
    "--owner",
    multiple=True,
    help="Filter out jobs by owner (multiple option).",
    secure=True,
)
@option("-n", "--name", metavar="NAME", help="Filter out jobs by name.", secure=True)
@option(
    "-t",
    "--tag",
    metavar="TAG",
    type=str,
    help="Filter out jobs by tag (multiple option)",
    multiple=True,
)
@option(
    "-d",
    "--description",
    metavar="DESCRIPTION",
    default="",
    help="Filter out jobs by description (exact match).",
    secure=True,
)
@option(
    "--since",
    metavar="DATE",
    help="Show jobs created after a specific date (including).",
)
@option(
    "--until",
    metavar="DATE",
    help="Show jobs created before a specific date (including).",
)
@option(
    "-a",
    "--all",
    is_flag=True,
    default=False,
    help=(
        "Show all jobs regardless the status (equivalent to "
        "`-s pending -s running -s succeeded -s failed`)."
    ),
)
@deprecated_quiet_option
@option("-w", "--wide", is_flag=True, help="Do not cut long lines for terminal width.")
@option(
    "--format",
    type=JOB_COLUMNS,
    help=(
        'Output table format, see "neuro help ps-format" '
        "for more info about the format specification. "
        "The default can be changed using the job.ps-format "
        'configuration variable documented in "neuro help user-config"'
    ),
    default=None,
)
@option("--full-uri", is_flag=True, help="Output full image URI.")
async def ls(
    root: Root,
    status: Sequence[str],
    all: bool,
    name: str,
    tag: Sequence[str],
    owner: Sequence[str],
    since: str,
    until: str,
    description: str,
    wide: bool,
    format: Optional[List[JobColumnInfo]],
    full_uri: bool,
) -> None:
    """
    List all jobs.

    Examples:

    neuro ps -a
    neuro ps -a --owner=user-1 --owner=user-2
    neuro ps --name my-experiments-v1 -s failed -s succeeded
    neuro ps --description="my favourite job"
    neuro ps -s failed -s succeeded -q
    neuro ps -t tag1 -t tag2
    """

    format = await calc_columns(root.client, format)

    statuses = calc_statuses(status, all)
    owners = set(owner)
    tags = set(tag)
    jobs = root.client.jobs.list(
        statuses=statuses,
        name=name,
        owners=owners,
        tags=tags,
        since=_parse_date(since),
        until=_parse_date(until),
    )

    # client-side filtering
    if description:
        jobs = (job async for job in jobs if job.description == description)

    uri_fmtr: URIFormatter
    if full_uri:
        uri_fmtr = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username, cluster_name=root.client.cluster_name
        )
    if root.quiet:
        formatter: BaseJobsFormatter = SimpleJobsFormatter()
    else:
        if wide or not root.tty:
            width = 0
        else:
            width = root.terminal_size[0]
        image_fmtr = image_formatter(uri_formatter=uri_fmtr)
        formatter = TabularJobsFormatter(
            width, root.client.username, format, image_formatter=image_fmtr
        )

    pager_maybe(formatter([job async for job in jobs]), root.tty, root.terminal_size)


@command()
@argument("job", type=JOB)
@option("--full-uri", is_flag=True, help="Output full URI.")
async def status(root: Root, job: str, full_uri: bool) -> None:
    """
    Display status of a job.
    """
    id = await resolve_job(
        job,
        client=root.client,
        status={
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
            JobStatus.FAILED,
        },
    )
    res = await root.client.jobs.status(id)
    uri_fmtr: URIFormatter
    if full_uri:
        uri_fmtr = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username, cluster_name=root.client.cluster_name
        )
    if root.tty:
        width = root.terminal_size[0]
    else:
        width = 0
    click.echo(JobStatusFormatter(uri_formatter=uri_fmtr, width=width)(res))


@command()
async def tags(root: Root) -> None:
    """
    List all tags submitted by the user.
    """
    res = await root.client.jobs.tags()
    pager_maybe(res, root.tty, root.terminal_size)


@command()
@click.argument("job", type=JOB)
async def browse(root: Root, job: str) -> None:
    """
    Opens a job's URL in a web browser.
    """
    id = await resolve_job(
        job, client=root.client, status={JobStatus.PENDING, JobStatus.RUNNING}
    )
    res = await root.client.jobs.status(id)
    await browse_job(root, res)


@command()
@argument("job", type=JOB)
@option(
    "--timeout",
    default=0,
    type=float,
    show_default=True,
    help="Maximum allowed time for executing the command, 0 for no timeout",
)
async def top(root: Root, job: str, timeout: float) -> None:
    """
    Display GPU/CPU/Memory usage.
    """
    formatter = JobTelemetryFormatter()
    id = await resolve_job(
        job, client=root.client, status={JobStatus.PENDING, JobStatus.RUNNING}
    )
    print_header = True
    async with async_timeout.timeout(timeout if timeout else None):
        async for res in root.client.jobs.top(id):
            if print_header:
                click.echo(formatter.header())
                print_header = False
            line = formatter(res)
            click.echo(f"\r{line}", nl=False)


@command()
@argument("job", type=JOB)
@argument("image", type=ImageType())
async def save(root: Root, job: str, image: RemoteImage) -> None:
    """
    Save job's state to an image.

    Examples:
    neuro job save job-id image:ubuntu-patched
    neuro job save my-favourite-job image:ubuntu-patched:v1
    neuro job save my-favourite-job image://bob/ubuntu-patched
    """
    id = await resolve_job(
        job,
        client=root.client,
        status={
            JobStatus.PENDING,
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.CANCELLED,
            JobStatus.FAILED,
        },
    )
    progress = DockerImageProgress.create(tty=root.tty, quiet=root.quiet)
    with contextlib.closing(progress):
        await root.client.jobs.save(id, image, progress=progress)
    click.echo(image)


@command()
@argument("jobs", nargs=-1, required=True, type=JOB)
async def kill(root: Root, jobs: Sequence[str]) -> None:
    """
    Kill job(s).
    """
    errors = []
    for job in jobs:
        job_resolved = await resolve_job(
            job, client=root.client, status={JobStatus.PENDING, JobStatus.RUNNING}
        )
        try:
            await root.client.jobs.kill(job_resolved)
            # TODO (ajuszkowski) printing should be on the cli level
            click.echo(job_resolved)
        except ValueError as e:
            errors.append((job, e))
        except AuthorizationError:
            errors.append((job, ValueError(f"Not enough permissions")))

    def format_fail(job: str, reason: Exception) -> str:
        return click.style(f"Cannot kill job {job}: {reason}", fg="red")

    for job, error in errors:
        click.echo(format_fail(job, error), err=True)
    if errors:
        sys.exit(1)


@command(context_settings=dict(allow_interspersed_args=False))
@argument("image", type=ImageType())
@argument("cmd", nargs=-1, type=click.UNPROCESSED)
@option(
    "-s",
    "--preset",
    type=PRESET,
    metavar="PRESET",
    help=(
        "Predefined resource configuration (to see available values, "
        "run `neuro config show`)"
    ),
)
@option(
    "-x/-X",
    "--extshm/--no-extshm",
    is_flag=True,
    default=True,
    show_default=True,
    help="Request extended '/dev/shm' space",
)
@option(
    "--http",
    type=int,
    metavar="PORT",
    default=80,
    show_default=True,
    help="Enable HTTP port forwarding to container",
)
@option(
    "--http-auth/--no-http-auth",
    is_flag=True,
    help="Enable HTTP authentication for forwarded HTTP port  [default: True]",
    default=None,
)
@option(
    "--preemptible/--non-preemptible",
    "-p/-P",
    help="Run job on a lower-cost preemptible instance (DEPRECATED AND IGNORED)",
    default=None,
    hidden=True,
)
@option(
    "-n",
    "--name",
    metavar="NAME",
    type=JOB_NAME,
    help="Optional job name",
    default=None,
    secure=True,
)
@option(
    "--tag",
    metavar="TAG",
    type=str,
    help="Optional job tag, multiple values allowed",
    multiple=True,
)
@option(
    "-d",
    "--description",
    metavar="DESC",
    help="Optional job description in free format",
    secure=True,
)
@deprecated_quiet_option
@option(
    "-v",
    "--volume",
    metavar="MOUNT",
    multiple=True,
    help=(
        "Mounts directory from vault into container. "
        "Use multiple options to mount more than one volume. "
        "Use --volume=ALL to mount all accessible storage directories. "
        "See `neuro help secrets` for information about "
        "passing secrets as mounted files."
    ),
    secure=True,
)
@option(
    "--entrypoint",
    type=str,
    help=(
        "Executable entrypoint in the container "
        "(note that it overwrites `ENTRYPOINT` and `CMD` "
        "instructions of the docker image)"
    ),
    secure=True,
)
@option(
    "-w",
    "--workdir",
    type=str,
    help="Working directory inside the container",
    secure=True,
)
@option(
    "-e",
    "--env",
    metavar="VAR=VAL",
    multiple=True,
    help=(
        "Set environment variable in container. "
        "Use multiple options to define more than one variable. "
        "See `neuro help secrets` for information about "
        "passing secrets as environment variables."
    ),
    secure=True,
)
@option(
    "--env-file",
    type=click.Path(exists=True),
    multiple=True,
    help="File with environment variables to pass",
    secure=True,
)
@option(
    "--restart",
    default="never",
    show_default=True,
    type=click.Choice([str(i) for i in JobRestartPolicy]),
    help="Restart policy to apply when a job exits",
)
@option(
    "--life-span",
    type=str,
    metavar="TIMEDELTA",
    help=(
        "Optional job run-time limit in the format '1d2h3m4s' "
        "(some parts may be missing). Set '0' to disable. "
        "Default value '1d' can be changed in the user config."
    ),
    show_default=True,
)
@option(
    "--schedule-timeout",
    type=str,
    metavar="TIMEDELTA",
    help=(
        "Optional job schedule timeout in the format '3m4s' "
        "(some parts may be missing)."
    ),
    show_default=True,
)
@option(
    "--wait-start/--no-wait-start",
    default=True,
    show_default=True,
    help="Wait for a job start or failure",
)
@option(
    "--pass-config/--no-pass-config",
    default=False,
    show_default=True,
    help="Upload neuro config to the job",
)
@option(
    "--port-forward",
    type=LOCAL_REMOTE_PORT,
    multiple=True,
    metavar="LOCAL_PORT:REMOTE_RORT",
    help="Forward port(s) of a running job to local port(s) "
    "(use multiple times for forwarding several ports)",
)
@option("--browse", is_flag=True, help="Open a job's URL in a web browser")
@option(
    "--detach",
    is_flag=True,
    help="Don't attach to job logs and don't wait for exit code",
)
@TTY_OPT
async def run(
    root: Root,
    image: RemoteImage,
    preset: str,
    extshm: bool,
    http: int,
    http_auth: Optional[bool],
    entrypoint: Optional[str],
    cmd: Sequence[str],
    workdir: Optional[str],
    volume: Sequence[str],
    env: Sequence[str],
    env_file: Sequence[str],
    restart: str,
    life_span: Optional[str],
    preemptible: Optional[bool],
    name: Optional[str],
    tag: Sequence[str],
    description: Optional[str],
    wait_start: bool,
    pass_config: bool,
    port_forward: List[Tuple[int, int]],
    browse: bool,
    detach: bool,
    tty: Optional[bool],
    schedule_timeout: Optional[str],
) -> None:
    """
    Run a job with predefined resources configuration.

    IMAGE docker image name to run in a job.

    CMD list will be passed as arguments to the executed job's image.

    Examples:

    # Starts a container pytorch:latest on a machine with smaller GPU resources
    # (see exact values in `neuro config show`) and with two volumes mounted:
    #   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
    #   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
    neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \\\\
        --volume=storage:/neuromation/public:/var/storage/home:ro pytorch:latest

    # Starts a container using the custom image my-ubuntu:latest stored in neuromation
    # registry, run /script.sh and pass arg1 and arg2 as its arguments:
    neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2
    """
    if not preset:
        preset = next(iter(root.client.config.presets.keys()))
    job_preset = root.client.config.presets[preset]
    if preemptible is not None:
        click.echo(
            "-p/-P option is deprecated and ignored. Use corresponding presets instead."
        )
    log.info(f"Using preset '{preset}': {job_preset}")
    if tty is None:
        tty = root.tty
    await run_job(
        root,
        image=image,
        gpu=job_preset.gpu,
        gpu_model=job_preset.gpu_model,
        tpu_type=job_preset.tpu_type,
        tpu_software_version=job_preset.tpu_software_version,
        cpu=job_preset.cpu,
        memory=job_preset.memory_mb,
        extshm=extshm,
        http=http,
        http_auth=http_auth,
        entrypoint=entrypoint,
        cmd=cmd,
        working_dir=workdir,
        volume=volume,
        env=env,
        env_file=env_file,
        restart=restart,
        life_span=life_span,
        port_forward=port_forward,
        preemptible=job_preset.is_preemptible,
        name=name,
        tags=tag,
        description=description,
        wait_start=wait_start,
        pass_config=pass_config,
        browse=browse,
        detach=detach,
        tty=tty,
        schedule_timeout=schedule_timeout,
    )


job.add_command(run)
job.add_command(submit)
job.add_command(ls)
job.add_command(status)
job.add_command(tags)
job.add_command(exec)
job.add_command(port_forward)
job.add_command(logs)
job.add_command(kill)
job.add_command(top)
job.add_command(save)
job.add_command(browse)
job.add_command(attach)


job.add_command(alias(ls, "list", hidden=True))
job.add_command(alias(logs, "monitor", hidden=True))


async def run_job(
    root: Root,
    *,
    image: RemoteImage,
    gpu: Optional[int],
    gpu_model: Optional[str],
    tpu_type: Optional[str],
    tpu_software_version: Optional[str],
    cpu: float,
    memory: int,
    extshm: bool,
    http: Optional[int],
    http_auth: Optional[bool],
    entrypoint: Optional[str],
    cmd: Sequence[str],
    working_dir: Optional[str],
    volume: Sequence[str],
    env: Sequence[str],
    env_file: Sequence[str],
    restart: str,
    life_span: Optional[str],
    port_forward: List[Tuple[int, int]],
    preemptible: bool,
    name: Optional[str],
    tags: Sequence[str],
    description: Optional[str],
    wait_start: bool,
    pass_config: bool,
    browse: bool,
    detach: bool,
    tty: bool,
    schedule_timeout: Optional[str],
) -> JobDescription:
    if http_auth is None:
        http_auth = True
    elif not http:
        if http_auth:
            raise click.UsageError("--http-auth requires --http")
        else:
            raise click.UsageError("--no-http-auth requires --http")
    if browse and not http:
        raise click.UsageError("--browse requires --http")
    if browse and not wait_start:
        raise click.UsageError("Cannot use --browse and --no-wait-start together")
    if not wait_start:
        detach = True
    if not detach:
        _check_tty(root, tty)

    job_restart_policy = JobRestartPolicy(restart)
    log.debug(f"Job restart policy: {job_restart_policy}")

    job_life_span = await calc_life_span(root.client, life_span)
    log.debug(f"Job run-time limit: {job_life_span}")

    if schedule_timeout is None:
        job_schedule_timeout = None
    else:
        job_schedule_timeout = _parse_timedelta(schedule_timeout).total_seconds()
    log.debug(f"Job schedule timeout: {job_schedule_timeout}")

    env_dict, secret_env_dict = root.client.parse.env(env, env_file)
    real_cmd = _parse_cmd(cmd)

    log.debug(f'entrypoint="{entrypoint}"')
    log.debug(f'cmd="{real_cmd}"')

    log.info(f"Using image '{image}'")

    if tpu_type:
        if not tpu_software_version:
            raise ValueError(
                "--tpu-sw-version cannot be empty while --tpu-type specified"
            )
    resources = Resources(
        memory_mb=memory,
        cpu=cpu,
        gpu=gpu,
        gpu_model=gpu_model,
        shm=extshm,
        tpu_type=tpu_type,
        tpu_software_version=tpu_software_version,
    )

    volumes, secret_files = root.client.parse.volumes(volume)

    if pass_config:
        env_name = NEURO_STEAL_CONFIG
        if env_name in env_dict:
            raise ValueError(f"{env_name} is already set to {env_dict[env_name]}")
        env_var, secret_volume = await upload_and_map_config(root)
        env_dict[NEURO_STEAL_CONFIG] = env_var
        volumes.append(secret_volume)

    if volumes:
        log.info(
            "Using volumes: \n"
            + "\n".join(f"  {volume_to_verbose_str(v)}" for v in volumes)
        )

    container = Container(
        image=image,
        entrypoint=entrypoint,
        command=real_cmd,
        working_dir=working_dir,
        http=HTTPPort(http, http_auth) if http else None,
        resources=resources,
        env=env_dict,
        volumes=list(volumes),
        secret_env=secret_env_dict,
        secret_files=list(secret_files),
        tty=tty,
    )

    job = await root.client.jobs.run(
        container,
        is_preemptible=preemptible,
        name=name,
        tags=tags,
        description=description,
        restart_policy=job_restart_policy,
        life_span=job_life_span,
        schedule_timeout=job_schedule_timeout,
    )
    progress = JobStartProgress.create(tty=root.tty, color=root.color, quiet=root.quiet)
    progress.begin(job)
    while wait_start and job.status == JobStatus.PENDING:
        await asyncio.sleep(0.2)
        job = await root.client.jobs.status(job.id)
        progress.step(job)
    progress.end(job)
    # Even if we detached, but the job has failed to start
    # (most common reason - no resources), the command fails
    if job.status == JobStatus.FAILED:
        sys.exit(job.history.exit_code or EX_PLATFORMERROR)

    if browse:
        await browse_job(root, job)

    if not detach:
        await process_attach(root, job, tty=tty, logs=True, port_forward=port_forward)

    return job


def _parse_cmd(cmd: Sequence[str]) -> str:
    if len(cmd) == 1:
        real_cmd = cmd[0]
    else:
        real_cmd = " ".join(shlex.quote(arg) for arg in cmd)
    return real_cmd


async def upload_and_map_config(root: Root) -> Tuple[str, Volume]:

    # store the Neuro CLI config on the storage under some random path
    nmrc_path = URL(root.config_path.expanduser().resolve().as_uri())
    random_nmrc_filename = f"{uuid.uuid4()}-cfg"
    storage_nmrc_folder = URL(
        f"storage://{root.client.cluster_name}/{root.client.username}/.neuro/"
    )
    storage_nmrc_path = storage_nmrc_folder / random_nmrc_filename
    local_nmrc_folder = f"{STORAGE_MOUNTPOINT}/.neuro/"
    local_nmrc_path = f"{local_nmrc_folder}{random_nmrc_filename}"
    if not root.quiet:
        click.echo(f"Temporary config file created on storage: {storage_nmrc_path}.")
        click.echo(f"Inside container it will be available at: {local_nmrc_path}.")
    await root.client.storage.mkdir(storage_nmrc_folder, parents=True, exist_ok=True)

    async def skip_tmp(fname: str) -> bool:
        return not fname.endswith(("-shm", "-wal", "-journal"))

    await root.client.storage.upload_dir(nmrc_path, storage_nmrc_path, filter=skip_tmp)
    # specify a container volume and mount the storage path
    # into specific container path
    return (
        local_nmrc_path,
        Volume(
            storage_uri=storage_nmrc_folder,
            container_path=local_nmrc_folder,
            read_only=False,
        ),
    )


async def browse_job(root: Root, job: JobDescription) -> None:
    url = job.http_url
    if url.scheme not in ("http", "https"):
        raise RuntimeError(f"Cannot browse job URL: {url}")
    click.echo(f"Browsing job, please open: {url}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, webbrowser.open, str(url))


def calc_statuses(status: Sequence[str], all: bool) -> Set[JobStatus]:
    defaults = {"running", "pending"}
    statuses = set(status)

    if "all" in statuses:
        if all:
            raise click.UsageError(
                "Parameters `-a/--all` and " "`-s all/--status=all` are incompatible"
            )
        click.echo(
            click.style(
                "DeprecationWarning: "
                "Option `-s all/--status=all` is deprecated. "
                "Please use `-a/--all` instead.",
                fg="red",
            ),
            err=True,
        )
        statuses = set()
    else:
        if all:
            if statuses:
                opt = " ".join([f"--status={s}" for s in status])
                log.warning(f"Option `-a/--all` overwrites option(s) `{opt}`")
            statuses = set()
        elif not statuses:
            statuses = defaults

    return set(JobStatus(s) for s in statuses)


async def calc_columns(
    client: Client, format: Optional[List[JobColumnInfo]]
) -> List[JobColumnInfo]:
    if format is None:
        config = await client.config.get_user_config()
        section = config.get("job")
        if section is not None:
            format_str = section.get("ps-format")
            if format_str is not None:
                return parse_columns(format_str)
        return get_default_columns()
    return format


async def calc_life_span(client: Client, value: Optional[str]) -> Optional[float]:
    async def _calc_default_life_span(client: Client) -> timedelta:
        config = await client.config.get_user_config()
        section = config.get("job")
        life_span = DEFAULT_JOB_LIFE_SPAN
        if section is not None:
            value = section.get("life-span")
            if value is not None:
                life_span = value
        return _parse_timedelta(life_span)

    delta = (
        _parse_timedelta(value)
        if value is not None
        else await _calc_default_life_span(client)
    )
    seconds = delta.total_seconds()
    if seconds == 0:
        return None
    assert seconds > 0
    return seconds


def _parse_timedelta(value: str) -> timedelta:
    value = value.strip()
    err = f"Could not parse time delta '{value}'"
    if value == "":
        raise click.UsageError(f"{err}: Empty string not allowed")
    if value == "0":
        return timedelta(0)
    match = REGEX_TIME_DELTA.search(value)
    if match is None:
        raise click.UsageError(
            f"{err}: Should be like '1d2h3m4s' (some parts may be missing)."
        )
    return timedelta(
        days=int(match.group("d") or 0),
        hours=int(match.group("h") or 0),
        minutes=int(match.group("m") or 0),
        seconds=int(match.group("s") or 0),
    )


def _parse_date(value: str) -> Optional[datetime]:
    if value:
        try:
            return isoparse(value)
        except ValueError:
            raise ValueError("Date should be in ISO-8601 format")
    else:
        return None


def _check_tty(root: Root, tty: bool) -> None:
    if tty and not root.tty:
        raise RuntimeError(
            "The operation should be executed from a terminal, "
            "the input device is not a TTY"
        )
