from datetime import datetime
from typing import Any, List, Union, cast

import pytest

from neuro_sdk import Action, BlobListing, BucketListing, PrefixListing

from neuro_cli.formatters.blob_storage import (
    BaseBlobFormatter,
    LongBlobFormatter,
    SimpleBlobFormatter,
)

ListResult = Union[BlobListing, PrefixListing]
LsResult = Union[BucketListing, BlobListing, PrefixListing]


class TestBlobFormatter:

    buckets = [
        BucketListing(
            name="neuro-my-bucket",
            creation_time=int(datetime(2018, 1, 1, 3).timestamp()),
            permission=Action.MANAGE,
        ),
        BucketListing(
            name="neuro-public-bucket",
            creation_time=int(datetime(2018, 1, 1, 13, 1, 5).timestamp()),
            permission=Action.READ,
        ),
        BucketListing(
            name="neuro-shared-bucket",
            creation_time=int(datetime(2018, 1, 1, 17, 2, 4).timestamp()),
            permission=Action.WRITE,
        ),
    ]

    blobs = [
        BlobListing(
            bucket_name="neuro-public-bucket",
            key="file1024.txt",
            modification_time=int(datetime(2018, 1, 1, 14, 0, 0).timestamp()),
            size=1024,
        ),
        BlobListing(
            bucket_name="neuro-public-bucket",
            key="file_bigger.txt",
            modification_time=int(datetime(2018, 1, 1).timestamp()),
            size=1_024_001,
        ),
        BlobListing(
            bucket_name="neuro-shared-bucket",
            key="folder2/info.txt",
            modification_time=int(datetime(2018, 1, 2).timestamp()),
            size=240,
        ),
        BlobListing(
            bucket_name="neuro-shared-bucket",
            key="folder2/",
            modification_time=int(datetime(2018, 1, 2).timestamp()),
            size=0,
        ),
    ]
    folders = [
        PrefixListing(bucket_name="neuro-public-bucket", prefix="folder1/"),
        PrefixListing(bucket_name="neuro-shared-bucket", prefix="folder2/"),
    ]

    list_results: List[ListResult] = cast(List[ListResult], blobs) + cast(
        List[ListResult], folders
    )
    files: List[ListResult] = []

    @pytest.mark.parametrize(
        "formatter",
        [
            (SimpleBlobFormatter(color=False)),
            (LongBlobFormatter(human_readable=False, color=False)),
        ],
    )
    def test_long_formatter(self, rich_cmp: Any, formatter: BaseBlobFormatter) -> None:
        formatter = LongBlobFormatter(human_readable=False, color=False)
        rich_cmp(formatter(self.list_results), index=0)
        rich_cmp(formatter(self.buckets), index=1)
        rich_cmp(formatter(self.files), index=2)
