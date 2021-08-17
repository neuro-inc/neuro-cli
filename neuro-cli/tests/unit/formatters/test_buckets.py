from typing import Any, List

import pytest
from dateutil.parser import isoparse

from neuro_sdk import Bucket

from neuro_cli.formatters.buckets import (
    BucketFormatter,
    BucketsFormatter,
    SimpleBucketsFormatter,
)
from neuro_cli.formatters.utils import format_datetime_human


def test_bucket_formatter(rich_cmp: Any) -> None:
    bucket = Bucket(
        id="bucket",
        name="test-bucket",
        owner="user",
        cluster_name="cluster",
        provider=Bucket.Provider.AWS,
        created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
    )
    fmtr = BucketFormatter(str, datetime_formatter=format_datetime_human)
    rich_cmp(fmtr(bucket))


@pytest.fixture
def buckets_list() -> List[Bucket]:
    return [
        Bucket(
            id="bucket-1",
            name="test-bucket",
            owner="user",
            cluster_name="cluster",
            created_at=isoparse("2017-03-04T12:28:59.759433+00:00"),
            provider=Bucket.Provider.AWS,
        ),
        Bucket(
            id="bucket-2",
            name="test-bucket-2",
            owner="user",
            cluster_name="cluster",
            created_at=isoparse("2016-03-04T12:28:59.759433+00:00"),
            provider=Bucket.Provider.AWS,
        ),
        Bucket(
            id="bucket-3",
            name=None,
            owner="user-2",
            cluster_name="cluster",
            created_at=isoparse("2018-03-04T12:28:59.759433+00:00"),
            provider=Bucket.Provider.AWS,
        ),
        Bucket(
            id="bucket-4",
            name=None,
            owner="user",
            cluster_name="cluster",
            created_at=isoparse("2019-03-04T12:28:59.759433+00:00"),
            provider=Bucket.Provider.AWS,
        ),
    ]


def test_buckets_formatter_simple(buckets_list: List[Bucket], rich_cmp: Any) -> None:
    fmtr = SimpleBucketsFormatter()
    rich_cmp(fmtr(buckets_list))


def test_buckets_formatter_short(buckets_list: List[Bucket], rich_cmp: Any) -> None:
    fmtr = BucketsFormatter(str, datetime_formatter=format_datetime_human)
    rich_cmp(fmtr(buckets_list))


def test_buckets_formatter_long(buckets_list: List[Bucket], rich_cmp: Any) -> None:
    fmtr = BucketsFormatter(
        str, long_format=True, datetime_formatter=format_datetime_human
    )
    rich_cmp(fmtr(buckets_list))
