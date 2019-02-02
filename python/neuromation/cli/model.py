import logging
from typing import List

import click
from yarl import URL

from neuromation.client import Image, NetworkPortForwarding, Resources
from neuromation.client.url_utils import normalize_storage_path_uri
from neuromation.strings.parse import to_megabytes_str

from .defaults import (
    GPU_MODELS,
    JOB_CPU_NUMBER,
    JOB_DEBUG_LOCAL_PORT,
    JOB_GPU_MODEL,
    JOB_GPU_NUMBER,
    JOB_MEMORY_AMOUNT,
)
from .formatter import JobFormatter
from .rc import Config
from .ssh_utils import remote_debug
from .utils import group, run_async


log = logging.getLogger(__name__)


@group(deprecated=True, hidden=True)
def model() -> None:
    """
    Model operations.
    """


@model.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("image")
@click.argument("dataset")
@click.argument("results")
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
@click.pass_obj
@run_async
async def train(
    cfg: Config,
    image: str,
    dataset: str,
    results: str,
    gpu: int,
    gpu_model: str,
    cpu: float,
    memory: str,
    extshm: bool,
    http: int,
    ssh: int,
    cmd: List[str],
    preemptible: bool,
    description: str,
    quiet: bool,
) -> None:
    """
    Start training job using model.

    The training job is created from IMAGE, dataset from DATASET and
    store output weights in RESULTS.

    COMMANDS list will be passed as commands to model container.
    """

    async with cfg.make_client() as client:
        try:
            dataset_url = normalize_storage_path_uri(URL(dataset), cfg.username)
        except ValueError:
            raise ValueError(
                f"Dataset path should be on platform. " f"Current value {dataset}"
            )

        try:
            resultset_url = normalize_storage_path_uri(URL(results), cfg.username)
        except ValueError:
            raise ValueError(
                f"Results path should be on platform. " f"Current value {results}"
            )

        network = NetworkPortForwarding.from_cli(http, ssh)
        memory = to_megabytes_str(memory)
        resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)

        cmdline = " ".join(cmd) if cmd is not None else None
        log.debug(f'cmdline="{cmdline}"')

        if not quiet:
            # TODO (ajuszkowski 01-Feb-19) normalize image name to URI (issue 452)
            log.info(f"Using image '{image}'")
            log.info(f"Using dataset '{dataset_url}'")
            log.info(f"Using weights '{resultset_url}'")

        image_obj = Image(image=image, command=cmdline)

        fmt = JobFormatter(quiet)

        res = await client.models.train(
            image=image_obj,
            resources=resources,
            dataset=dataset_url,
            results=resultset_url,
            description=description,
            network=network,
            is_preemptible=preemptible,
        )
        job = await client.jobs.status(res.id)
        click.echo(fmt(job))


@model.command()
@click.pass_obj
@click.argument("id")
@click.option(
    "--localport",
    type=int,
    help="Local port number for debug",
    default=JOB_DEBUG_LOCAL_PORT,
    show_default=True,
)
@run_async
async def debug(cfg: Config, id: str, localport: int) -> None:
    """
    Starts ssh terminal connected to running job.

    Job should be started with SSH support enabled.

    Examples:

    neuro model debug --localport 12789 job-abc-def-ghk
    """
    git_key = cfg.github_rsa_path

    async with cfg.make_client() as client:
        await remote_debug(client, id, git_key, localport)
