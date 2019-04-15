import asyncio
import logging
import os
import shlex
import sys
from typing import List, Sequence, Tuple

import click

from neuromation.api import (
    DockerImage,
    Image,
    ImageNameParser,
    JobStatus,
    NetworkPortForwarding,
    Resources,
    Volume,
)
from neuromation.cli.utils import LOCAL_REMOTE_PORT
from neuromation.strings.parse import to_megabytes_str

from .defaults import (
    GPU_MODELS,
    JOB_CPU_NUMBER,
    JOB_GPU_MODEL,
    JOB_GPU_NUMBER,
    JOB_MEMORY_AMOUNT,
)
from .formatters import (
    BaseJobsFormatter,
    JobFormatter,
    JobStartProgress,
    JobStatusFormatter,
    JobTelemetryFormatter,
    SimpleJobsFormatter,
    TabularJobsFormatter,
)
from .root import Root
from .utils import (
    ImageType,
    alias,
    async_cmd,
    command,
    group,
    resolve_job,
    volume_to_verbose_str,
)


log = logging.getLogger(__name__)


@group()
def job() -> None:
    """
    Job operations.
    """


@command(context_settings=dict(ignore_unknown_options=True))
@click.argument("image", type=ImageType())
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED)
@click.option(
    "-g",
    "--gpu",
    metavar="NUMBER",
    type=int,
    help="Number of GPUs to request",
    default=JOB_GPU_NUMBER,
    show_default=True,
)
@click.option(
    "--gpu-model",
    metavar="MODEL",
    type=click.Choice(GPU_MODELS),
    help="GPU to use",
    default=JOB_GPU_MODEL,
    show_default=True,
)
@click.option(
    "-c",
    "--cpu",
    metavar="NUMBER",
    type=float,
    help="Number of CPUs to request",
    default=JOB_CPU_NUMBER,
    show_default=True,
)
@click.option(
    "-m",
    "--memory",
    metavar="AMOUNT",
    type=str,
    help="Memory amount to request",
    default=JOB_MEMORY_AMOUNT,
    show_default=True,
)
@click.option(
    "-x/-X",
    "--extshm/--no-extshm",
    is_flag=True,
    default=True,
    show_default=True,
    help="Request extended '/dev/shm' space",
)
@click.option("--http", type=int, help="Enable HTTP port forwarding to container")
@click.option(
    "--http-auth/--no-http-auth",
    is_flag=True,
    help="Enable HTTP authentication for forwarded HTTP port",
    default=True,
    show_default=True,
)
@click.option(
    "--preemptible/--non-preemptible",
    "-p/-P",
    help="Run job on a lower-cost preemptible instance",
    default=True,
    show_default=True,
)
@click.option(
    "-n",
    "--name",
    metavar="NAME",
    type=str,
    help="Optional job name",
    default=None,
    show_default=True,
)
@click.option(
    "-d",
    "--description",
    metavar="DESC",
    help="Optional job description in free format",
)
@click.option(
    "-q", "--quiet", is_flag=True, help="Run command in quiet mode (print only job id)"
)
@click.option(
    "-v",
    "--volume",
    metavar="MOUNT",
    multiple=True,
    help="Mounts directory from vault into container. "
    "Use multiple options to mount more than one volume",
)
@click.option(
    "-e",
    "--env",
    metavar="VAR=VAL",
    multiple=True,
    help="Set environment variable in container "
    "Use multiple options to define more than one variable",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="File with environment variables to pass",
)
@click.option(
    "--wait-start/--no-wait-start",
    default=True,
    show_default=True,
    help="Wait for a job start or failure",
)
@async_cmd()
async def submit(
    root: Root,
    image: DockerImage,
    gpu: int,
    gpu_model: str,
    cpu: float,
    memory: str,
    extshm: bool,
    http: int,
    http_auth: bool,
    cmd: Sequence[str],
    volume: Sequence[str],
    env: Sequence[str],
    env_file: str,
    preemptible: bool,
    name: str,
    description: str,
    quiet: bool,
    wait_start: bool,
) -> None:
    """
    Submit an image to run on the cluster.

    IMAGE container image name.

    CMD list will be passed as commands to model container.

    Examples:

    # Starts a container pytorch:latest with two paths mounted. Directory /q1/
    # is mounted in read only mode to /qm directory within container.
    # Directory /mod mounted to /mod directory in read-write mode.
    neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw \
      pytorch:latest
    """

    username = root.username

    # TODO (Alex Davydow 12.12.2018): Consider splitting env logic into
    # separate function.
    if env_file:
        with open(env_file, "r") as ef:
            env = ef.read().splitlines() + list(env)

    env_dict = {}
    for line in env:
        splitted = line.split("=", 1)
        if len(splitted) == 1:
            val = os.environ.get(splitted[0], "")
            env_dict[splitted[0]] = val
        else:
            env_dict[splitted[0]] = splitted[1]

    cmd = " ".join(cmd) if cmd is not None else None
    log.debug(f'cmd="{cmd}"')

    memory = to_megabytes_str(memory)

    # TODO (ajuszkowski 01-Feb-19) process --quiet globally to set up logger+click
    if not quiet:
        log.info(f"Using image '{image.as_url_str()}'")
        log.debug(f"IMAGE: {image}")
    image_obj = Image(image=image.as_repo_str(), command=cmd)

    network = NetworkPortForwarding.from_cli(http, http_auth)
    resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)
    volumes = Volume.from_cli_list(username, volume)
    if volumes and not quiet:
        log.info(
            "Using volumes: \n"
            + "\n".join(f"  {volume_to_verbose_str(v)}" for v in volumes)
        )

    job = await root.client.jobs.submit(
        image=image_obj,
        resources=resources,
        network=network,
        volumes=volumes,
        is_preemptible=preemptible,
        name=name,
        description=description,
        env=env_dict,
    )
    click.echo(JobFormatter(quiet)(job))
    progress = JobStartProgress.create(tty=root.tty, color=root.color, quiet=quiet)
    while wait_start and job.status == JobStatus.PENDING:
        await asyncio.sleep(0.2)
        job = await root.client.jobs.status(job.id)
        progress(job)
    progress.close()


@command(context_settings=dict(ignore_unknown_options=True))
@click.argument("job")
@click.argument("cmd", nargs=-1, type=click.UNPROCESSED, required=True)
@click.option(
    "-t",
    "--tty",
    is_flag=True,
    help="Allocate virtual tty. Useful for interactive jobs.",
)
@click.option(
    "--no-key-check",
    is_flag=True,
    help="Disable host key checks. Should be used with caution.",
)
@async_cmd()
async def exec(
    root: Root, job: str, tty: bool, no_key_check: bool, cmd: Sequence[str]
) -> None:
    """
    Execute command in a running job.
    """
    cmd = shlex.split(" ".join(cmd))
    id = await resolve_job(root.client, job)
    retcode = await root.client.jobs.exec(id, tty, no_key_check, cmd)
    sys.exit(retcode)


@command(context_settings=dict(ignore_unknown_options=True))
@click.argument("job")
@click.argument("local_remote_port", type=LOCAL_REMOTE_PORT, nargs=-1)
@click.option(
    "--no-key-check",
    is_flag=True,
    help="Disable host key checks. Should be used with caution.",
)
@async_cmd()
async def port_forward(
    root: Root, job: str, no_key_check: bool, local_remote_port: List[Tuple[int, int]]
) -> None:
    """
    Forward port(s) of a running job to local port(s).
    """
    loop = asyncio.get_event_loop()
    job_id = await resolve_job(root.client, job)
    tasks = []
    for local_port, remote_port in local_remote_port:
        print(f"Port of {job_id} will be forwarded to localhost:{local_port}")
        tasks.append(
            loop.create_task(
                root.client.jobs.port_forward(
                    job_id, no_key_check, local_port, remote_port
                )
            )
        )

    print("Press ^C to stop forwarding")
    result = 0
    for future in asyncio.as_completed(tasks):
        try:
            await future
        except ValueError as e:
            print(f"Port forwarding failed: {e}")
            [task.cancel() for task in tasks]
            result = -1
            break

    sys.exit(result)


@command()
@click.argument("job")
@async_cmd()
async def logs(root: Root, job: str) -> None:
    """
    Print the logs for a container.
    """
    id = await resolve_job(root.client, job)
    async for chunk in root.client.jobs.monitor(id):
        if not chunk:
            break
        click.echo(chunk.decode(errors="ignore"), nl=False)


@command()
@click.option(
    "-s",
    "--status",
    multiple=True,
    type=click.Choice(["pending", "running", "succeeded", "failed", "all"]),
    help="Filter out job by status (multiple option)",
)
@click.option("-n", "--name", metavar="NAME", help="Filter out jobs by name")
@click.option(
    "-d",
    "--description",
    metavar="DESCRIPTION",
    help="Filter out jobs by description (exact match)",
)
@click.option("-q", "--quiet", is_flag=True, help="Print only Job ID")
@click.option(
    "-w", "--wide", is_flag=True, help="Do not cut long lines for terminal width"
)
@async_cmd()
async def ls(
    root: Root,
    status: Sequence[str],
    name: str,
    description: str,
    quiet: bool,
    wide: bool,
) -> None:
    """
    List all jobs.

    Examples:

    neuro ps --name my-experiments-v1 --status all
    neuro ps --description="my favourite job"
    neuro ps -s failed -s succeeded -q
    """

    status = status or ["running", "pending"]

    # TODO: add validation of status values
    statuses = set(status)
    if "all" in statuses:
        statuses = set()

    jobs = await root.client.jobs.list(statuses, name)

    # client-side filtering
    if description:
        jobs = [job for job in jobs if job.description == description]

    jobs.sort(key=lambda job: job.history.created_at)

    if quiet:
        formatter: BaseJobsFormatter = SimpleJobsFormatter()
    else:
        if wide or not root.tty:
            width = 0
        else:
            width = root.terminal_size[0]
        image_parser = ImageNameParser(root.username, root.registry_url)
        formatter = TabularJobsFormatter(width, image_parser)

    for line in formatter(jobs):
        click.echo(line)


@command()
@click.argument("job")
@async_cmd()
async def status(root: Root, job: str) -> None:
    """
    Display status of a job.
    """
    id = await resolve_job(root.client, job)
    res = await root.client.jobs.status(id)
    click.echo(JobStatusFormatter()(res))


@command()
@click.argument("job")
@async_cmd()
async def top(root: Root, job: str) -> None:
    """
    Display GPU/CPU/Memory usage.
    """
    formatter = JobTelemetryFormatter()
    id = await resolve_job(root.client, job)
    print_header = True
    async for res in root.client.jobs.top(id):
        if print_header:
            click.echo(formatter.header())
            print_header = False
        line = formatter(res)
        click.echo(f"\r{line}", nl=False)


@command()
@click.argument("jobs", nargs=-1, required=True)
@async_cmd()
async def kill(root: Root, jobs: Sequence[str]) -> None:
    """
    Kill job(s).
    """
    errors = []
    for job in jobs:
        job_resolved = await resolve_job(root.client, job)
        try:
            await root.client.jobs.kill(job_resolved)
            # TODO (ajuszkowski) printing should be on the cli level
            print(job_resolved)
        except ValueError as e:
            errors.append((job, e))

    def format_fail(job: str, reason: Exception) -> str:
        return f"Cannot kill job {job}: {reason}"

    for job, error in errors:
        click.echo(format_fail(job, error))


job.add_command(submit)
job.add_command(ls)
job.add_command(status)
job.add_command(exec)
job.add_command(port_forward)
job.add_command(logs)
job.add_command(kill)
job.add_command(top)


job.add_command(alias(ls, "list", hidden=True))
job.add_command(alias(logs, "monitor", hidden=True))
