from typing import Any, List

import pytest

from neuro_sdk import Bucket

from neuro_cli.formatters.buckets import (
    BucketFormatter,
    BucketsFormatter,
    SimpleBucketsFormatter,
)


def test_bucket_formatter(rich_cmp: Any) -> None:
    bucket = Bucket(
        id="bucket",
        name="test-bucket",
        owner="user",
        cluster_name="cluster",
        provider=Bucket.Provider.AWS,
        credentials={"test": "value"},
    )
    fmtr = BucketFormatter(str)
    rich_cmp(fmtr(bucket))


@pytest.fixture
def buckets_list() -> List[Bucket]:
    return [
        Bucket(
            id="bucket-1",
            name="test-bucket",
            owner="user",
            cluster_name="cluster",
            provider=Bucket.Provider.AWS,
            credentials={"test": "value"},
        ),
        Bucket(
            id="bucket-2",
            name="test-bucket-2",
            owner="user",
            cluster_name="cluster",
            provider=Bucket.Provider.AWS,
            credentials={"test": "value"},
        ),
        Bucket(
            id="bucket-3",
            name=None,
            owner="user-2",
            cluster_name="cluster",
            provider=Bucket.Provider.AWS,
            credentials={"test": "value"},
        ),
        Bucket(
            id="bucket-4",
            name=None,
            owner="user",
            cluster_name="cluster",
            provider=Bucket.Provider.AWS,
            credentials={"test": "value"},
        ),
    ]


def test_buckets_formatter_simple(buckets_list: List[Bucket], rich_cmp: Any) -> None:
    fmtr = SimpleBucketsFormatter()
    rich_cmp(fmtr(buckets_list))


def test_buckets_formatter(buckets_list: List[Bucket], rich_cmp: Any) -> None:
    fmtr = BucketsFormatter(str)
    rich_cmp(fmtr(buckets_list))
