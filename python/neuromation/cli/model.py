import logging
from typing import List

import click
from yarl import URL

from neuromation.client import Image, NetworkPortForwarding, Resources
from neuromation.strings.parse import to_megabytes_str

from . import rc
from .defaults import DEFAULTS, GPU_MODELS
from .formatter import OutputFormatter
from .ssh_utils import remote_debug
from .utils import Context, run_async


log = logging.getLogger(__name__)


@click.group()
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
    type=float,
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
@click.pass_obj
@run_async
async def train(
    ctx: Context,
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

    async with ctx.make_client() as client:
        try:
            dataset_url = client.cfg.norm_storage(URL(dataset))
        except ValueError:
            raise ValueError(
                f"Dataset path should be on platform. " f"Current value {dataset}"
            )

        try:
            resultset_url = client.cfg.norm_storage(URL(results))
        except ValueError:
            raise ValueError(
                f"Results path should be on platform. " f"Current value {results}"
            )

        network = NetworkPortForwarding.from_cli(http, ssh)
        memory = to_megabytes_str(memory)
        resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)

        cmdline = " ".join(cmd) if cmd is not None else None
        log.debug(f'cmdline="{cmdline}"')

        image_obj = Image(image=image, command=cmdline)

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
        click.echo(OutputFormatter().format_job(job, quiet))


@model.command()
@click.pass_obj
@click.argument("id")
@click.option(
    "--localport",
    type=int,
    help="Local port number for debug",
    default=DEFAULTS["model_debug_local_port"],
    show_default=True,
)
@run_async
async def debug(ctx: Context, id: str, localport: int) -> None:
    """
    Starts ssh terminal connected to running job.

    Job should be started with SSH support enabled.

    Examples:

    \b
    neuro model debug --localport 12789 job-abc-def-ghk
    """
    config = rc.ConfigFactory.load()
    git_key = config.github_rsa_path

    async with ctx.make_client() as client:
        await remote_debug(client, id, git_key, localport)
