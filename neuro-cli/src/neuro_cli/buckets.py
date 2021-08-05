from typing import Optional, Sequence

from neuro_cli.click_types import BUCKET, BUCKET_NAME, CLUSTER
from neuro_cli.utils import resolve_bucket

from .formatters.buckets import (
    BaseBucketsFormatter,
    BucketFormatter,
    BucketsFormatter,
    SimpleBucketsFormatter,
)
from .formatters.utils import URIFormatter, get_datetime_formatter, uri_formatter
from .root import Root
from .utils import argument, command, group, option


@group()
def bucket() -> None:
    """
    Operations with buckets.
    """


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Look on a specified cluster (the current cluster by default).",
)
@option("--full-uri", is_flag=True, help="Output full bucket URI.")
@option("--long-format", is_flag=True, help="Output all info about bucket.")
async def ls(
    root: Root, full_uri: bool, long_format: bool, cluster: Optional[str]
) -> None:
    """
    List buckets.
    """
    if root.quiet:
        buckets_fmtr: BaseBucketsFormatter = SimpleBucketsFormatter()
    else:
        if full_uri:
            uri_fmtr: URIFormatter = str
        else:
            uri_fmtr = uri_formatter(
                username=root.client.username,
                cluster_name=cluster or root.client.cluster_name,
            )
        buckets_fmtr = BucketsFormatter(
            uri_fmtr,
            datetime_formatter=get_datetime_formatter(root.iso_datetime_format),
            long_format=long_format,
        )

    buckets = []
    with root.status("Fetching buckets") as status:
        async with root.client.buckets.list(cluster_name=cluster) as it:
            async for bucket in it:
                buckets.append(bucket)
                status.update(f"Fetching buckets ({len(buckets)} loaded)")

    with root.pager():
        root.print(buckets_fmtr(buckets))


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Perform in a specified cluster (the current cluster by default).",
)
@option(
    "--name",
    type=BUCKET_NAME,
    metavar="NAME",
    help="Optional bucket name",
    default=None,
)
async def create(
    root: Root,
    name: Optional[str] = None,
    cluster: Optional[str] = None,
) -> None:
    """
    Create a new bucket.
    """
    bucket = await root.client.buckets.create(
        name=name,
        cluster_name=cluster,
    )
    bucket_fmtr = BucketFormatter(
        str, datetime_formatter=get_datetime_formatter(root.iso_datetime_format)
    )
    with root.pager():
        root.print(bucket_fmtr(bucket))


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Look on a specified cluster (the current cluster by default).",
)
@argument("bucket", type=BUCKET)
@option("--full-uri", is_flag=True, help="Output full bucket URI.")
async def get(root: Root, cluster: Optional[str], bucket: str, full_uri: bool) -> None:
    """
    Get bucket BUCKET_ID.
    """
    bucket_id = await resolve_bucket(bucket, client=root.client, cluster_name=cluster)
    bucket_obj = await root.client.buckets.get(bucket_id, cluster_name=cluster)
    if full_uri:
        uri_fmtr: URIFormatter = str
    else:
        uri_fmtr = uri_formatter(
            username=root.client.username,
            cluster_name=cluster or root.client.cluster_name,
        )
    bucket_fmtr = BucketFormatter(
        uri_fmtr, datetime_formatter=get_datetime_formatter(root.iso_datetime_format)
    )
    with root.pager():
        root.print(bucket_fmtr(bucket_obj))


@command()
@option(
    "--cluster",
    type=CLUSTER,
    help="Perform on a specified cluster (the current cluster by default).",
)
@argument("buckets", type=BUCKET, nargs=-1, required=True)
async def rm(root: Root, cluster: Optional[str], buckets: Sequence[str]) -> None:
    """
    Remove bucket DISK_ID.
    """
    for bucket in buckets:
        bucket_id = await resolve_bucket(
            bucket, client=root.client, cluster_name=cluster
        )
        await root.client.buckets.rm(bucket_id, cluster_name=cluster)
        if root.verbosity >= 0:
            root.print(f"Bucket with id '{bucket_id}' was successfully removed.")


bucket.add_command(ls)
bucket.add_command(create)
bucket.add_command(get)
bucket.add_command(rm)
