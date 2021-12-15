import abc
import operator
from typing import Sequence

from rich import box
from rich.console import RenderableType, RenderGroup
from rich.table import Table
from rich.text import Text

from neuro_sdk import Bucket

from neuro_cli.click_types import ORG
from neuro_cli.formatters.utils import DatetimeFormatter, URIFormatter


class BaseBucketsFormatter:
    @abc.abstractmethod
    def __call__(self, buckets: Sequence[Bucket]) -> RenderableType:
        pass


class SimpleBucketsFormatter(BaseBucketsFormatter):
    def __call__(self, buckets: Sequence[Bucket]) -> RenderableType:
        return RenderGroup(*(Text(bucket.id) for bucket in buckets))


class BucketsFormatter(BaseBucketsFormatter):
    def __init__(
        self,
        uri_formatter: URIFormatter,
        datetime_formatter: DatetimeFormatter,
        *,
        long_format: bool = False,
    ) -> None:
        self._uri_formatter = uri_formatter
        self._datetime_formatter = datetime_formatter
        self._long_format = long_format

    def _bucket_to_table_row(self, bucket: Bucket) -> Sequence[str]:
        line = [
            bucket.id,
            bucket.name or "",
            bucket.provider + (" (imported)" if bucket.imported else ""),
            self._uri_formatter(bucket.uri),
        ]
        if self._long_format:
            line += [
                bucket.org_name or ORG.NO_ORG_STR,
                self._datetime_formatter(bucket.created_at),
                "√" if bucket.public else "×",
            ]
        return line

    def __call__(self, buckets: Sequence[Bucket]) -> RenderableType:
        buckets = sorted(buckets, key=operator.attrgetter("id"))
        table = Table(box=box.SIMPLE_HEAVY)
        # make sure that the first column is fully expanded
        width = len("bucket-06bed296-8b27-4aa8-9e2a-f3c47b41c807")
        table.add_column("Id", style="bold", width=width)
        table.add_column("Name")
        table.add_column("Provider")
        table.add_column("Uri")
        if self._long_format:
            table.add_column("Org name")
            table.add_column("Created at")
            table.add_column("Public")
        for bucket in buckets:
            table.add_row(*self._bucket_to_table_row(bucket))
        return table


class BucketFormatter:
    def __init__(
        self, uri_formatter: URIFormatter, datetime_formatter: DatetimeFormatter
    ) -> None:
        self._datetime_formatter = datetime_formatter
        self._uri_formatter = uri_formatter

    def __call__(self, bucket: Bucket) -> RenderableType:
        table = Table(
            box=None,
            show_header=False,
            show_edge=False,
        )
        table.add_column()
        table.add_column(style="bold")
        table.add_row("Id", bucket.id)
        table.add_row("Uri", self._uri_formatter(bucket.uri))
        if bucket.name:
            table.add_row("Name", bucket.name)
        table.add_row("Org name", bucket.org_name or ORG.NO_ORG_STR)
        table.add_row("Created at", self._datetime_formatter(bucket.created_at))
        table.add_row("Provider", bucket.provider)
        table.add_row("Imported", str(bucket.imported))
        table.add_row("Public", str(bucket.public))
        return table
