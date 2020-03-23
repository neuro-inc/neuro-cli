import configparser
import json
import os
import pathlib
from typing import IO, Optional

import click
import yaml

from neuromation.api.admin import _ClusterUserRoleType

from .formatters import ClustersFormatter, ClusterUserFormatter
from .formatters.config import QuotaFormatter
from .root import Root
from .utils import argument, command, group, option, pager_maybe


@group()
def admin() -> None:
    """Cluster administration commands."""


@command()
async def get_clusters(root: Root) -> None:
    """
    Print the list of available clusters.
    """
    fmt = ClustersFormatter()
    clusters = await root.client._admin.list_clusters()
    pager_maybe(
        fmt(clusters.values()), root.tty, root.terminal_size,
    )


@command()
@argument("cluster_name", required=True, type=str)
@argument("config", required=True, type=click.File(encoding="utf8", lazy=False))
async def add_cluster(root: Root, cluster_name: str, config: IO[str]) -> None:
    """
    Create a new cluster and start its provisioning.
    """
    config_dict = yaml.safe_load(config)
    await root.client._admin.add_cluster(cluster_name, config_dict)
    if not root.quiet:
        click.echo(
            f"Cluster {cluster_name} successfully added "
            "and will be set up within 24 hours"
        )


@command()
@argument(
    "config",
    required=False,
    type=click.Path(exists=False, path_type=str),
    default="cluster.yml",
)
@option("--type", prompt="Select cluster type", type=click.Choice(["aws", "gcp"]))
async def generate_cluster_config(root: Root, config: str, type: str) -> None:
    """
    Create a cluster configuration file.
    """
    config_path = pathlib.Path(config)
    if config_path.exists():
        raise ValueError(
            f"Config path {config_path} already exists, "
            "please remove the file or pass the new file name explicitly."
        )
    if type == "aws":
        content = await generate_aws()
    elif type == "gcp":
        content = await generate_gcp()
    else:
        assert False, "Prompt should prevent this case"
    config_path.write_text(content, encoding="utf-8")
    if not root.quiet:
        click.echo(f"Cluster config {config_path} is generated.")


AWS_TEMPLATE = """\
type: aws
region: us-east-1
zones:
- us-east-1a
- us-east-1b
vpc_id: {vpc_id}
credentials:
  access_key_id: {access_key_id}
  secret_access_key: {secret_access_key}
node_pools:
- id: m5_2xlarge
  min_size: 1
  max_size: 4
- id: p2_xlarge_1x_nvidia_tesla_k80
  min_size: 1
  max_size: 4
- id: p3_2xlarge_1x_nvidia_tesla_v100
  min_size: 0
  max_size: 1
storage:
  id: generalpurpose_bursting
"""


async def generate_aws() -> str:
    args = {}
    args["vpc_id"] = click.prompt("AWS VPC ID")
    access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if access_key_id is None or secret_access_key is None:
        aws_config_file = pathlib.Path(
            os.environ.get("AWS_SHARED_CREDENTIALS_FILE", "~/.aws/credentials")
        )
        aws_config_file = aws_config_file.expanduser().absolute()
        parser = configparser.ConfigParser()
        parser.read(aws_config_file)
        profile = click.prompt(
            "AWS profile name", default=os.environ.get("AWS_PROFILE", "default")
        )
        if access_key_id is None:
            access_key_id = parser[profile]["aws_access_key_id"]
        if secret_access_key is None:
            secret_access_key = parser[profile]["aws_secret_access_key"]
    access_key_id = click.prompt("AWS Access Key", default=access_key_id)
    secret_access_key = click.prompt("AWS Secret Key", default=secret_access_key)
    args["access_key_id"] = access_key_id
    args["secret_access_key"] = secret_access_key
    return AWS_TEMPLATE.format_map(args)


GCP_TEMPLATE = """\
type: gcp
location_type: multi_zonal
region: us-central1
zones:
- us-central1-a
- us-central1-c
project: {project_name}
credentials: {credentials}
node_pools:
- id: n1_highmem_8
  min_size: 1
  max_size: 4
- id: n1_highmem_8_1x_nvidia_tesla_k80
  min_size: 1
  max_size: 4
- id: n1_highmem_8_1x_nvidia_tesla_v100
  min_size: 0
  max_size: 1
storage:
  id: gcs-nfs
"""


async def generate_gcp() -> str:
    args = {}
    args["project_name"] = click.prompt("GCP project name")
    credentials_file = click.prompt(
        "Service Account Key File (.json)",
        default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    )
    with open(credentials_file, "rb") as fp:
        data = json.load(fp)
    out = yaml.dump(data)
    args["credentials"] = "\n" + "\n".join("  " + line for line in out.splitlines())
    return GCP_TEMPLATE.format_map(args)


@command()
@argument("cluster_name", required=False, default=None, type=str)
async def get_cluster_users(root: Root, cluster_name: Optional[str]) -> None:
    """
    Print the list of all users in the cluster with their assigned role.
    """
    fmt = ClusterUserFormatter()
    clusters = await root.client._admin.list_cluster_users(cluster_name)
    pager_maybe(fmt(clusters), root.tty, root.terminal_size)


@command()
@argument("cluster_name", required=True, type=str)
@argument("user_name", required=True, type=str)
@argument(
    "role",
    required=False,
    default=_ClusterUserRoleType.USER.value,
    metavar="[ROLE]",
    type=click.Choice(list(_ClusterUserRoleType)),
)
async def add_cluster_user(
    root: Root, cluster_name: str, user_name: str, role: str
) -> None:
    """
    Add user access to specified cluster.

    The command supports one of 3 user roles: admin, manager or user.
    """
    user = await root.client._admin.add_cluster_user(cluster_name, user_name, role)
    if not root.quiet:
        click.echo(
            f"Added {click.style(user.user_name, bold=True)} to cluster "
            f"{click.style(cluster_name, bold=True)} as "
            f"{click.style(user.role, bold=True)}"
        )


def _parse_quota_value(
    value: Optional[str], allow_infinity: bool = False
) -> Optional[int]:
    if value is None:
        return None
    try:
        if value[-1] not in ("h", "m"):
            raise ValueError(f"Unable to parse: '{value}'")
        result = float(value[:-1]) * {"h": 60, "m": 1}[value[-1]]
        if result < 0:
            raise ValueError(f"Negative quota values ({value}) are not allowed")
        if result == float("inf"):
            if allow_infinity:
                return None
            else:
                raise ValueError("Infinite quota values are not allowed")
    except (ValueError, LookupError):
        raise
    return int(result)


@command()
@argument("cluster_name", required=True, type=str)
@argument("user_name", required=True, type=str)
async def remove_cluster_user(root: Root, cluster_name: str, user_name: str) -> None:
    """
    Remove user access from the cluster.
    """
    await root.client._admin.remove_cluster_user(cluster_name, user_name)
    if not root.quiet:
        click.echo(
            f"Removed {click.style(user_name, bold=True)} from cluster "
            f"{click.style(cluster_name, bold=True)}"
        )


@command()
@argument("cluster_name", required=True, type=str)
@argument("user_name", required=True, type=str)
@option(
    "-g",
    "--gpu",
    metavar="AMOUNT",
    type=str,
    help="GPU quota value in hours (h) or minutes (m).",
)
@option(
    "-n",
    "--non-gpu",
    metavar="AMOUNT",
    type=str,
    help="Non-GPU quota value in hours (h) or minutes (m).",
)
async def set_user_quota(
    root: Root,
    cluster_name: str,
    user_name: str,
    gpu: Optional[str],
    non_gpu: Optional[str],
) -> None:
    """
    Set user quota to given values
    """
    gpu_value_minutes = _parse_quota_value(gpu, allow_infinity=True)
    non_gpu_value_minutes = _parse_quota_value(non_gpu, allow_infinity=True)
    user_with_quota = await root.client._admin.set_user_quota(
        cluster_name, user_name, gpu_value_minutes, non_gpu_value_minutes
    )
    fmt = QuotaFormatter()
    click.echo(
        f"New quotas for {click.style(user_with_quota.user_name, underline=True)} "
        f"on cluster {click.style(cluster_name, underline=True)}:"
    )
    click.echo(fmt(user_with_quota.quota))


@command()
@argument("cluster_name", required=True, type=str)
@argument("user_name", required=True, type=str)
@option(
    "-g",
    "--gpu",
    metavar="AMOUNT",
    type=str,
    help="Additional GPU quota value in hours (h) or minutes (m).",
)
@option(
    "-n",
    "--non-gpu",
    metavar="AMOUNT",
    type=str,
    help="Additional non-GPU quota value in hours (h) or minutes (m).",
)
async def add_user_quota(
    root: Root,
    cluster_name: str,
    user_name: str,
    gpu: Optional[str],
    non_gpu: Optional[str],
) -> None:
    """
    Add given values to user quota
    """
    additional_gpu_value_minutes = _parse_quota_value(gpu, False)
    additional_non_gpu_value_minutes = _parse_quota_value(non_gpu, False)
    user_with_quota = await root.client._admin.add_user_quota(
        cluster_name,
        user_name,
        additional_gpu_value_minutes,
        additional_non_gpu_value_minutes,
    )
    fmt = QuotaFormatter()
    click.echo(
        f"New quotas for {click.style(user_with_quota.user_name, underline=True)} "
        f"on cluster {click.style(cluster_name, underline=True)}:"
    )
    click.echo(fmt(user_with_quota.quota))


admin.add_command(get_clusters)
admin.add_command(generate_cluster_config)
admin.add_command(add_cluster)

admin.add_command(get_cluster_users)
admin.add_command(add_cluster_user)
admin.add_command(remove_cluster_user)

admin.add_command(set_user_quota)
admin.add_command(add_user_quota)
