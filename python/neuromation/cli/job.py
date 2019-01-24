import shlex
import logging
import os
from typing import List

import click
from neuromation.clientv2 import Image, NetworkPortForwarding, Resources, Volume

from . import rc
from .default import DEFAULTS, GPU_MODELS
from .utils import Context
from neuromation.strings.parse import to_megabytes_str
from .formatter import OutputFormatter

log = logging.getLogger(__name__)
import sys


@click.group()
def job() -> None:
    """
    Model operations.
    """


@job.command()
@click.argument("image")
@click.argument("cmd", nargs=-1)
@click.option(
    "-g",
    "--gpu",
    metavar="NUMBER",
    type=int,
    help="Number of GPUs to request",
    default=DEFAULTS["model_train_gpu_number"],
    show_default=True,
)
@click.option(
    "--gpu-model",
    metavar="MODEL",
    type=click.Choice(GPU_MODELS),
    help="GPU to use",
    default=DEFAULTS["model_train_gpu_model"],
    show_default=True,
)
@click.option(
    "-c",
    "--cpu",
    metavar="NUMBER",
    type=int,
    help="Number of CPUs to request",
    default=DEFAULTS["model_train_cpu_number"],
    show_default=True,
)
@click.option(
    "-m",
    "--memory",
    metavar="AMOUNT",
    type=str,
    help="Memory amount to request",
    default=DEFAULTS["model_train_memory_amount"],
    show_default=True,
)
@click.option("-x", "--extshm", is_flag=True, help="Request extended '/dev/shm' space")
@click.option("--http", type=int, help="Enable HTTP port forwarding to container")
@click.option("--ssh", type=int, help="Enable SSH port forwarding to container")
@click.option(
    "--preemptible/--non-preemptible",
    help="Run job on a lower-cost preemptible instance",
    default=True,
)
@click.option(
    "-d", "--description", metavar="DESC", help="Add optional description to the job"
)
@click.option(
    "-q", "--quiet", is_flag=True, help="Run command in quiet mode (print only job id)"
)
@click.option(
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
@click.pass_obj
@run_async
async def submit(
    ctx: Context,
    image: str,
    gpu: int,
    gpu_model: str,
    cpu: int,
    memory: str,
    extshm: bool,
    http: int,
    ssh: int,
    cmd: List[str],
    volume: List[str],
    env: List[str],
    env_file: str,
    preemptible: bool,
    description: str,
    quiet: bool,
):
    """
    Start job using IMAGE.

    COMMANDS list will be passed as commands to model container.

    Examples:

    \b
    # Starts a container pytorch:latest with two paths mounted. Directory /q1/
    # is mounted in read only mode to /qm directory within container.
    # Directory /mod mounted to /mod directory in read-write mode.
    neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw \
    pytorch:latest

    \b
    # Starts a container pytorch:latest with connection enabled to port 22 and
    # sets PYTHONPATH environment value to /python.
    # Please note that SSH server should be provided by container.
    neuro job submit --env PYTHONPATH=/python --volume \
    storage:/data/2018q1:/data:ro --ssh 22 pytorch:latest
    """

    config = rc.ConfigFactory.load()
    username = config.get_platform_user_name()

    # TODO (Alex Davydow 12.12.2018): Consider splitting env logic into
    # separate function.
    if env_file:
        with open(env_file, "r") as ef:
            env = ef.read().splitlines() + env

    env_dict = {}
    for line in env:
        splited = line.split("=", 1)
        if len(splited) == 1:
            val = os.environ.get(splited[0], "")
            env_dict[splited[0]] = val
        else:
            env_dict[splited[0]] = splited[1]

    cmd = " ".join(cmd) if cmd is not None else None
    log.debug(f'cmd="{cmd}"')

    memory = to_megabytes_str(memory)
    image = Image(image=image, command=cmd)
    network = NetworkPortForwarding.from_cli(http, ssh)
    resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)
    volumes = Volume.from_cli_list(username, volume)

    async with ctx.make_client() as client:
        job = await client.jobs.submit(
            image=image,
            resources=resources,
            network=network,
            volumes=volumes,
            is_preemptible=preemptible,
            description=description,
            env=env_dict,
        )
        click.echo(OutputFormatter.format_job(job, quiet))


@job.command()
async def exec(id: str, tty: bool, no_key_check: bool, cmd: List[str])-> None:
    """
    Usage:
        neuro job exec [options] ID CMD...

    Executes command in a running job.

    Options:
        -t, --tty         Allocate virtual tty. Useful for interactive jobs.
        --no-key-check    Disable host key checks. Should be used with caution.
    """
    cmd = shlex.split(" ".join(cmd))
    async with ctx.make_client() as client:
        retcode = await client.jobs.exec(id, tty, no_key_check, cmd)
    sys.exit(retcode)


@command
async def ssh(id, user, key):
    """
    Usage:
        neuro job ssh [options] ID

    Starts ssh terminal connected to running job.
    Job should be started with SSH support enabled.

    Options:
        --user STRING         Container user name [default: {job_ssh_user}]
        --key STRING          Path to container private key.

    Examples:
    neuro job ssh --user alfa --key ./my_docker_id_rsa job-abc-def-ghk
    """
    config: Config = rc.ConfigFactory.load()
    git_key = config.github_rsa_path

    async with ClientV2(url, token) as client:
        await connect_ssh(client, id, git_key, user, key)


@command
async def monitor(id):
    """
    Usage:
        neuro job monitor ID

    Monitor job output stream
    """
    timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=None, sock_connect=30
    )

    async with ClientV2(url, token, timeout=timeout) as client:
        async for chunk in client.jobs.monitor(id):
            if not chunk:
                break
            sys.stdout.write(chunk.decode(errors="ignore"))


@command
async def list(status, description, quiet):
    """
    Usage:
        neuro job list [options]

    Options:
      -s, --status (pending|running|succeeded|failed|all)
          Filter out job by status(es) (comma delimited if multiple)
      -d, --description DESCRIPTION
          Filter out job by job description (exact match)
      -q, --quiet
          Run command in quiet mode (print only job ids)

    List all jobs

    Examples:
    neuro job list --description="my favourite job"
    neuro job list --status=all
    neuro job list --status=pending,running --quiet
    """

    status = status or "running,pending"

    # TODO: add validation of status values
    statuses = set(status.split(","))
    if "all" in statuses:
        statuses = set()

    async with ClientV2(url, token) as client:
        jobs = await client.jobs.list()

    formatter = JobListFormatter(quiet=quiet)
    return formatter.format_jobs(jobs, statuses, description)


@command
async def status(id):
    """
    Usage:
        neuro job status ID

    Display status of a job
    """
    async with ClientV2(url, token) as client:
        res = await client.jobs.status(id)
        return JobStatusFormatter.format_job_status(res)


@command
async def kill(job_ids):
    """
    Usage:
        neuro job kill JOB_IDS...

    Kill job(s)
    """
    errors = []
    async with ClientV2(url, token) as client:
        for job in job_ids:
            try:
                await client.jobs.kill(job)
                print(job)
            except ValueError as e:
                errors.append((job, e))

    def format_fail(job: str, reason: Exception) -> str:
        return f"Cannot kill job {job}: {reason}"

    for job, error in errors:
        print(format_fail(job, error))
