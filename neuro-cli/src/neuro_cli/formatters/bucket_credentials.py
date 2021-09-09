import abc
import operator
from typing import Awaitable, Callable, Sequence

from rich import box
from rich.console import RenderableType, RenderGroup
from rich.styled import Styled
from rich.table import Table
from rich.text import Text

from neuro_sdk import Bucket, PersistentBucketCredentials


class BaseBucketCredentialsFormatter:
    @abc.abstractmethod
    async def __call__(
        self, credentials: Sequence[PersistentBucketCredentials]
    ) -> RenderableType:
        pass


class SimpleBucketCredentialsFormatter(BaseBucketCredentialsFormatter):
    async def __call__(
        self, credentials: Sequence[PersistentBucketCredentials]
    ) -> RenderableType:
        return RenderGroup(*(Text(credential.id) for credential in credentials))


class BucketCredentialsFormatter(BaseBucketCredentialsFormatter):
    def __init__(self, get_bucket: Callable[[str], Awaitable[Bucket]]):
        self._get_bucket = get_bucket

    async def _credential_to_table_row(
        self, credential: PersistentBucketCredentials
    ) -> Sequence[str]:
        buckets = [
            await self._get_bucket(credential.bucket_id)
            for credential in credential.credentials
        ]
        line = [
            credential.id,
            credential.name or "",
            ", ".join(bucket.name or bucket.id for bucket in buckets),
            "√" if credential.read_only else "×",
        ]
        return line

    async def __call__(
        self, credentials: Sequence[PersistentBucketCredentials]
    ) -> RenderableType:
        credentials = sorted(credentials, key=operator.attrgetter("id"))
        table = Table(box=box.SIMPLE_HEAVY)
        # make sure that the first column is fully expanded
        width = len("bucket-credentials-06bed296-8b27-4aa8-9e2a-f3c47b41c807")
        table.add_column("Id", style="bold", width=width)
        table.add_column("Name")
        table.add_column("Buckets")
        table.add_column("Read-only")
        for credential in credentials:
            table.add_row(*(await self._credential_to_table_row(credential)))
        return table


class BucketCredentialFormatter:
    def __init__(self, get_bucket: Callable[[str], Awaitable[Bucket]]):
        self._get_bucket = get_bucket

    async def __call__(self, credential: PersistentBucketCredentials) -> RenderableType:
        table = Table(
            box=None,
            show_header=False,
            show_edge=False,
        )
        table.add_column()
        table.add_column(style="bold")
        table.add_row("Id", credential.id)
        if credential.name:
            table.add_row("Name", credential.name)

        table.add_row("Read-only:", str(credential.read_only))

        for bucket_credential in credential.credentials:
            credentials = Table(box=None, show_header=True, show_edge=False)
            credentials.add_column("Key")
            credentials.add_column("Value")
            for key, value in bucket_credential.credentials.items():
                credentials.add_row(key, value)
            bucket = await self._get_bucket(bucket_credential.bucket_id)
            table.add_row(
                f"Credentials for bucket '{bucket.name or bucket.id}'",
                Styled(credentials, style="reset"),
            )
        return table
