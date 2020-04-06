from datetime import datetime
from typing import List, Union, cast

import pytest

from neuromation.api import Action, BlobListing, BucketListing, PrefixListing
from neuromation.cli.formatters import (
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

    list_results: List[ListResult] = (
        cast(List[ListResult], blobs) + cast(List[ListResult], folders)
    )

    def test_simple_formatter(self) -> None:
        formatter = SimpleBlobFormatter(color=False)
        assert list(formatter(self.list_results)) == [
            "blob:neuro-public-bucket/file1024.txt",
            "blob:neuro-public-bucket/file_bigger.txt",
            "blob:neuro-shared-bucket/folder2/info.txt",
            "blob:neuro-shared-bucket/folder2/",
            "blob:neuro-public-bucket/folder1/",
            "blob:neuro-shared-bucket/folder2/",
        ]
        assert list(formatter(self.buckets)) == [
            "blob:neuro-my-bucket",
            "blob:neuro-public-bucket",
            "blob:neuro-shared-bucket",
        ]

    def test_long_formatter(self) -> None:
        formatter = LongBlobFormatter(human_readable=False, color=False)
        assert list(formatter(self.list_results)) == [
            "    1024 2018-01-01 14:00:00 blob:neuro-public-bucket/file1024.txt",
            " 1024001 2018-01-01 00:00:00 blob:neuro-public-bucket/file_bigger.txt",
            "     240 2018-01-02 00:00:00 blob:neuro-shared-bucket/folder2/info.txt",
            "       0 2018-01-02 00:00:00 blob:neuro-shared-bucket/folder2/",
            "                             blob:neuro-public-bucket/folder1/",
            "                             blob:neuro-shared-bucket/folder2/",
        ]
        assert list(formatter(self.buckets)) == [
            "m  2018-01-01 03:00:00 blob:neuro-my-bucket",
            "r  2018-01-01 13:01:05 blob:neuro-public-bucket",
            "w  2018-01-01 17:02:04 blob:neuro-shared-bucket",
        ]

        formatter = LongBlobFormatter(human_readable=True, color=False)
        assert list(formatter(self.list_results)) == [
            "    1.0K 2018-01-01 14:00:00 blob:neuro-public-bucket/file1024.txt",
            " 1000.0K 2018-01-01 00:00:00 blob:neuro-public-bucket/file_bigger.txt",
            "     240 2018-01-02 00:00:00 blob:neuro-shared-bucket/folder2/info.txt",
            "       0 2018-01-02 00:00:00 blob:neuro-shared-bucket/folder2/",
            "                             blob:neuro-public-bucket/folder1/",
            "                             blob:neuro-shared-bucket/folder2/",
        ]

        assert list(formatter(self.buckets)) == [
            "m  2018-01-01 03:00:00 blob:neuro-my-bucket",
            "r  2018-01-01 13:01:05 blob:neuro-public-bucket",
            "w  2018-01-01 17:02:04 blob:neuro-shared-bucket",
        ]

    @pytest.mark.parametrize(
        "formatter",
        [
            (SimpleBlobFormatter(color=False)),
            (LongBlobFormatter(human_readable=False, color=False)),
        ],
    )
    def test_formatter_with_empty_files(self, formatter: BaseBlobFormatter) -> None:
        files: List[LsResult] = []
        assert [] == list(formatter(files))
