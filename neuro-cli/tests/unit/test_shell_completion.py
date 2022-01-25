import logging
import os
import shlex
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, AsyncIterator, Callable, List, Optional, Sequence, Tuple
from unittest import mock

import pytest
from dateutil.parser import isoparse
from yarl import URL

from neuro_sdk import (
    Action,
    BlobObject,
    Bucket,
    Container,
    FileStatus,
    FileStatusType,
    JobDescription,
    Jobs,
    JobStatus,
    JobStatusHistory,
    RemoteImage,
    Resources,
    Storage,
)
from neuro_sdk._buckets import Buckets
from neuro_sdk._url_utils import normalize_storage_path_uri
from neuro_sdk._utils import asyncgeneratorcontextmanager

from .conftest import SysCapWithCode

JOB_OUTPUT_TIMEOUT = 10 * 60
NETWORK_TIMEOUT = 3 * 60.0
_RunCli = Callable[[Sequence[str]], SysCapWithCode]

log = logging.getLogger(__name__)


def _default_args(verbosity: int, network_timeout: float, nmrc_path: Path) -> List[str]:
    args = [
        "--show-traceback",
        "--disable-pypi-version-check",
        "--color=no",
        f"--network-timeout={network_timeout}",
        "--skip-stats",
        f"--neuromation-config={nmrc_path}",
    ]

    if verbosity < 0:
        args.append("-" + "q" * (-verbosity))
    if verbosity > 0:
        args.append("-" + "v" * verbosity)

    return args


def autocomplete(
    run_cli: _RunCli,
    nmrc_path: Path,
    monkeypatch: Any,
    arguments: Sequence[str],
    *,
    shell: str,
    verbosity: int = 0,
    network_timeout: float = NETWORK_TIMEOUT,
    timeout: float = JOB_OUTPUT_TIMEOUT,
) -> str:
    __tracebackhide__ = True

    log.info("Run 'neuro %s'", " ".join(arguments))

    args = _default_args(verbosity, network_timeout, nmrc_path)
    env = dict(os.environ)

    env["_PYTEST_COMPLETE"] = f"{shell}_complete"
    env["COMP_WORDS"] = " ".join(shlex.quote(arg) for arg in [*args, *arguments])
    env["COMP_CWORD"] = str(len(args) + len(arguments) - 1)
    env["NEURO_CLI_JOB_AUTOCOMPLETE_LIMIT"] = "500"

    monkeypatch.setattr(os, "environ", env)
    proc = run_cli([])
    assert proc.code == 0
    assert not proc.err
    return proc.out


_RunAC = Callable[[List[str]], Tuple[str, str]]


@pytest.fixture()
def run_autocomplete(run_cli: _RunCli, nmrc_path: Path, monkeypatch: Any) -> _RunAC:
    def autocompleter(args: Sequence[str]) -> Tuple[str, str]:
        zsh_out = autocomplete(run_cli, nmrc_path, monkeypatch, args, shell="zsh")
        bash_out = autocomplete(run_cli, nmrc_path, monkeypatch, args, shell="bash")
        return zsh_out, bash_out

    return autocompleter


skip_on_windows = pytest.mark.skipif(
    sys.platform == "win32", reason="Autocompletion is not supported on Windows"
)


@skip_on_windows
def test_file_autocomplete(run_autocomplete: _RunAC, tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    (base / "file.txt").write_bytes(b"")
    (base / "folder").mkdir()
    (base / "folder/file2.txt").write_bytes(b"")
    (base / "folder/folder2").mkdir()

    zsh_out, bash_out = run_autocomplete(["storage", "cp", "fi"])
    assert bash_out == "uri,file:,"
    assert zsh_out == "uri\nfile:\n_\n_"

    base_uri = base.as_uri()
    base_prefix = base_uri[5:]
    names = os.listdir(base)
    names = [name + ("/" if "folder" in name else "") for name in names]

    zsh_out, bash_out = run_autocomplete(["storage", "cp", base_uri + "/"])
    assert bash_out == "\n".join(f"uri,{name},{base_prefix}/" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\n{base_uri}/" for name in names)

    zsh_out, bash_out = run_autocomplete(["storage", "cp", base_uri + "/f"])
    assert bash_out == "\n".join(f"uri,{name},{base_prefix}/" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\n{base_uri}/" for name in names)

    zsh_out, bash_out = run_autocomplete(["storage", "cp", base_uri + "/fi"])
    assert bash_out == f"uri,file.txt,{base_prefix}/"
    assert zsh_out == f"uri\nfile.txt\n_\n{base_uri}/"

    zsh_out, bash_out = run_autocomplete(["storage", "cp", base_uri + "/folder"])
    assert bash_out == f"uri,folder/,{base_prefix}/"
    assert zsh_out == f"uri\nfolder/\n_\n{base_uri}/"

    zsh_out, bash_out = run_autocomplete(["storage", "cp", base_uri + "/folder/"])
    names = os.listdir(base / "folder")
    names = [name + ("/" if "folder" in name else "") for name in names]
    assert bash_out == "\n".join(f"uri,{name},{base_prefix}/folder/" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\n{base_uri}/folder/" for name in names)


@skip_on_windows
def test_file_autocomplete_default(run_autocomplete: _RunAC) -> None:
    default = Path.cwd().parent
    default_uri = default.as_uri()
    default_prefix = default_uri[5:]
    names = [p.name + ("/" if p.is_dir() else "") for p in default.iterdir()]
    zsh_out, bash_out = run_autocomplete(["storage", "cp", "file:"])
    assert bash_out == "\n".join(f"uri,{name},{default_prefix}/" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\n{default_uri}/" for name in names)

    cwd = Path.cwd()
    cwd_uri = cwd.as_uri()
    cwd_prefix = cwd_uri[5:]
    names = [p.name + ("/" if p.is_dir() else "") for p in cwd.iterdir()]
    zsh_out, bash_out = run_autocomplete(["storage", "cp", "file://"])
    assert bash_out == "\n".join(f"uri,{name},{cwd_prefix}/" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\n{cwd_uri}/" for name in names)


@skip_on_windows
def test_file_autocomplete_root(run_autocomplete: _RunAC) -> None:
    names = [p.name + ("/" if p.is_dir() else "") for p in Path("/").iterdir()]
    zsh_out, bash_out = run_autocomplete(["storage", "cp", "file:/"])
    assert bash_out == "\n".join(f"uri,{name},////" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\nfile:////" for name in names)

    zsh_out, bash_out = run_autocomplete(["storage", "cp", "file:///"])
    assert bash_out == "\n".join(f"uri,{name},////" for name in names)
    assert zsh_out == "\n".join(f"uri\n{name}\n_\nfile:////" for name in names)


@skip_on_windows
def test_storage_autocomplete(run_autocomplete: _RunAC) -> None:
    with mock.patch.object(Storage, "stat") as mocked_stat, mock.patch.object(
        Storage, "list"
    ) as mocked_list:

        tree = {
            URL("storage://default"): ["test-user", "other-user"],
            URL("storage://default/test-user"): ["folder", "file.txt"],
            URL("storage://default/test-user/folder/"): ["folder2", "file2.txt"],
            URL("storage://default/other-user/"): ["folder3", "file3.txt"],
            URL("storage://other-cluster"): ["test-user"],
        }

        def is_dir(uri: URL) -> bool:
            return ".txt" not in uri.name

        async def stat(uri: URL) -> FileStatus:
            uri = normalize_storage_path_uri(uri, "test-user", "default", org_name=None)
            if uri.path.endswith("/") and uri.path != "/":
                uri = uri.with_path(uri.path.rstrip("/"))
            return FileStatus(
                path=uri.path,
                type=FileStatusType.DIRECTORY if is_dir(uri) else FileStatusType.FILE,
                size=0,
                modification_time=1234567890,
                permission=Action.WRITE,
                uri=uri,
            )

        @asyncgeneratorcontextmanager
        async def list(uri: URL) -> AsyncIterator[FileStatus]:
            uri = normalize_storage_path_uri(uri, "test-user", "default", org_name=None)
            for name in tree[uri]:
                child = uri / name
                yield FileStatus(
                    path=name,
                    type=FileStatusType.DIRECTORY
                    if is_dir(child)
                    else FileStatusType.FILE,
                    size=0,
                    modification_time=1234567890,
                    permission=Action.WRITE,
                    uri=child,
                )

        mocked_stat.side_effect = stat
        mocked_list.side_effect = list

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "st"])
        assert bash_out == "uri,storage:,"
        assert zsh_out == "uri\nstorage:\n_\n_"

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:"])
        assert bash_out == ("uri,folder/,\n" "uri,file.txt,")
        assert zsh_out == ("uri\nfolder/\n_\nstorage:\n" "uri\nfile.txt\n_\nstorage:")

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:f"])
        assert bash_out == ("uri,folder/,\n" "uri,file.txt,")
        assert zsh_out == ("uri\nfolder/\n_\nstorage:\n" "uri\nfile.txt\n_\nstorage:")

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:folder/"])
        assert bash_out == ("uri,folder2/,folder/\n" "uri,file2.txt,folder/")
        assert zsh_out == (
            "uri\nfolder2/\n_\nstorage:folder/\n" "uri\nfile2.txt\n_\nstorage:folder/"
        )

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:folder/fi"])
        assert bash_out == "uri,file2.txt,folder/"
        assert zsh_out == "uri\nfile2.txt\n_\nstorage:folder/"

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:/"])
        assert bash_out == ""
        assert zsh_out == ""

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage:/test-user/"])
        assert bash_out == ""
        assert zsh_out == ""

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage://"])
        assert bash_out == ""
        assert zsh_out == ""

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage://d"])
        assert bash_out == "uri,default/,//"
        assert zsh_out == "uri\ndefault/\n_\nstorage://"

        zsh_out, bash_out = run_autocomplete(["storage", "cp", "storage://default/"])
        assert bash_out == ""
        assert zsh_out == ""


@skip_on_windows
def test_blob_autocomplete(run_autocomplete: _RunAC) -> None:
    with mock.patch.object(Buckets, "list") as mocked_list, mock.patch.object(
        Buckets, "blob_is_dir"
    ) as mocked_blob_is_dir, mock.patch.object(
        Buckets, "list_blobs"
    ) as mocked_list_blobs:

        @asyncgeneratorcontextmanager
        async def list(cluster_name: str) -> AsyncIterator[Bucket]:
            yield Bucket(
                id="bucket-1",
                name="neuro-my-bucket",
                created_at=datetime(2018, 1, 1, 3),
                cluster_name="test-cluster",
                owner="test-user",
                provider=Bucket.Provider.AWS,
                imported=False,
                org_name=None,
            )
            yield Bucket(
                id="bucket-2",
                name="neuro-public-bucket",
                created_at=datetime(2018, 1, 1, 17, 2, 4),
                cluster_name="test-cluster",
                owner="public",
                provider=Bucket.Provider.AWS,
                imported=False,
                org_name=None,
            )
            yield Bucket(
                id="bucket-3",
                name="neuro-shared-bucket",
                created_at=datetime(2018, 1, 1, 13, 1, 5),
                cluster_name="test-cluster",
                owner="another-user",
                provider=Bucket.Provider.AWS,
                imported=False,
                org_name=None,
            )

        async def blob_is_dir(uri: URL) -> bool:
            return ".txt" not in uri.name

        @asyncgeneratorcontextmanager
        async def list_blobs(uri: URL) -> AsyncIterator[BlobObject]:
            async with list(uri.host) as it:
                async for bucket in it:
                    break
                else:
                    return
            yield BlobObject(
                key="file1024.txt",
                modified_at=datetime(2018, 1, 1, 14, 0, 0),
                bucket=bucket,
                size=1024,
            )
            yield BlobObject(
                key="file_bigger.txt",
                modified_at=datetime(2018, 1, 1, 14, 0, 0),
                bucket=bucket,
                size=1_024_001,
            )
            yield BlobObject(
                key="folder2/info.txt",
                modified_at=datetime(2018, 1, 1, 14, 0, 0),
                bucket=bucket,
                size=240,
            )
            yield BlobObject(
                key="folder2/",
                modified_at=datetime(2018, 1, 1, 14, 0, 0),
                bucket=bucket,
                size=0,
            )

        mocked_list.side_effect = list
        mocked_blob_is_dir.side_effect = blob_is_dir
        mocked_list_blobs.side_effect = list_blobs

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "bl"])
        assert bash_out == "uri,blob:,"
        assert zsh_out == "uri\nblob:\n_\n_"

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:"])
        assert bash_out == (
            "uri,bucket-1/,\n"
            "uri,neuro-my-bucket/,\n"
            "uri,bucket-2/,\n"
            "uri,neuro-public-bucket/,\n"
            "uri,bucket-3/,\n"
            "uri,neuro-shared-bucket/,"
        )
        assert zsh_out == (
            "uri\nbucket-1/\n_\nblob:\nuri\nneuro-my-bucket/\n_\nblob:\n"
            "uri\nbucket-2/\n_\nblob:\n"
            "uri\nneuro-public-bucket/\n_\nblob:\n"
            "uri\nbucket-3/\n_\nblob:\n"
            "uri\nneuro-shared-bucket/\n_\nblob:"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:b"])
        assert bash_out == ("uri,bucket-1/,\n" "uri,bucket-2/,\n" "uri,bucket-3/,")
        assert zsh_out == (
            "uri\nbucket-1/\n_\nblob:\n"
            "uri\nbucket-2/\n_\nblob:\n"
            "uri\nbucket-3/\n_\nblob:"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:n"])
        assert bash_out == (
            "uri,neuro-my-bucket/,\n"
            "uri,neuro-public-bucket/,\n"
            "uri,neuro-shared-bucket/,"
        )
        assert zsh_out == (
            "uri\nneuro-my-bucket/\n_\nblob:\n"
            "uri\nneuro-public-bucket/\n_\nblob:\n"
            "uri\nneuro-shared-bucket/\n_\nblob:"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1"])
        assert bash_out == "uri,bucket-1/,"
        assert zsh_out == "uri\nbucket-1/\n_\nblob:"

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1/"])
        assert bash_out == (
            "uri,file1024.txt,bucket-1/\n"
            "uri,file_bigger.txt,bucket-1/\n"
            "uri,info.txt,bucket-1/\n"
            "uri,folder2/,bucket-1/"
        )
        assert zsh_out == (
            "uri\nfile1024.txt\n_\nblob:bucket-1/\n"
            "uri\nfile_bigger.txt\n_\nblob:bucket-1/\n"
            "uri\ninfo.txt\n_\nblob:bucket-1/\n"
            "uri\nfolder2/\n_\nblob:bucket-1/"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1/f"])
        assert bash_out == (
            "uri,file1024.txt,bucket-1/\n"
            "uri,file_bigger.txt,bucket-1/\n"
            "uri,folder2/,bucket-1/"
        )
        assert zsh_out == (
            "uri\nfile1024.txt\n_\nblob:bucket-1/\n"
            "uri\nfile_bigger.txt\n_\nblob:bucket-1/\n"
            "uri\nfolder2/\n_\nblob:bucket-1/"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1/fi"])
        assert bash_out == (
            "uri,file1024.txt,bucket-1/\n" "uri,file_bigger.txt,bucket-1/"
        )
        assert zsh_out == (
            "uri\nfile1024.txt\n_\nblob:bucket-1/\n"
            "uri\nfile_bigger.txt\n_\nblob:bucket-1/"
        )

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1/folder2"])
        assert bash_out == "uri,folder2/,bucket-1/"
        assert zsh_out == "uri\nfolder2/\n_\nblob:bucket-1/"

        zsh_out, bash_out = run_autocomplete(["blob", "ls", "blob:bucket-1/folder2/"])
        assert bash_out == (
            "uri,file1024.txt,bucket-1/folder2/\n"
            "uri,file_bigger.txt,bucket-1/folder2/\n"
            "uri,info.txt,bucket-1/folder2/\n"
            "uri,folder2/,bucket-1/folder2/"
        )
        assert zsh_out == (
            "uri\nfile1024.txt\n_\nblob:bucket-1/folder2/\n"
            "uri\nfile_bigger.txt\n_\nblob:bucket-1/folder2/\n"
            "uri\ninfo.txt\n_\nblob:bucket-1/folder2/\n"
            "uri\nfolder2/\n_\nblob:bucket-1/folder2/"
        )


def make_job(
    job_id: str,
    name: str = None,
    owner: str = "test-user",
    cluster_name: str = "default",
) -> JobDescription:
    return JobDescription(
        status=JobStatus.FAILED,
        owner=owner,
        cluster_name=cluster_name,
        id=job_id,
        name=name,
        uri=URL(f"job://{cluster_name}/{owner}/{job_id}"),
        description=None,
        history=JobStatusHistory(
            status=JobStatus.FAILED,
            reason="ErrorReason",
            description="ErrorDesc",
            created_at=isoparse("2018-09-25T12:28:21.298672+00:00"),
            started_at=isoparse("2018-09-25T12:28:59.759433+00:00"),
            finished_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        ),
        container=Container(
            command="test-command",
            image=RemoteImage.new_external_image(name="test-image"),
            resources=Resources(16, 0.1, 0, None, True, None, None),
        ),
        scheduler_enabled=False,
        pass_config=False,
        preset_name="testing",
        total_price_credits=Decimal("150"),
        price_credits_per_hour=Decimal("15"),
    )


@skip_on_windows
def test_job_autocomplete(run_autocomplete: _RunAC) -> None:
    with mock.patch.object(Jobs, "list") as mocked_list:
        jobs = [
            make_job("job-0123-4567"),
            make_job("job-89ab-cdef", name="jeronimo"),
            make_job("job-0123-cdef", owner="other-user"),
            make_job("job-89ab-4567", cluster_name="other-cluster"),
        ]

        @asyncgeneratorcontextmanager
        async def list(
            since: Optional[datetime] = None,
            reverse: bool = False,
            limit: Optional[int] = None,
        ) -> AsyncIterator[JobDescription]:
            for job in jobs:
                yield job

        mocked_list.side_effect = list

        zsh_out, bash_out = run_autocomplete(["job", "status", "j"])
        assert bash_out == (
            "plain,job-0123-4567,\n"
            "plain,job:job-0123-4567,\n"
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job-89ab-cdef,\n"
            "plain,jeronimo,\n"
            "plain,job:job-89ab-cdef,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job-0123-cdef,\n"
            "plain,job:job-0123-cdef,\n"
            "plain,job:/other-user/job-0123-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,\n"
            "plain,job-89ab-4567,\n"
            "plain,job:job-89ab-4567,\n"
            "plain,job:/test-user/job-89ab-4567,\n"
            "plain,job://other-cluster/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob-0123-4567\n_\n_\n"
            "plain\njob:job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob-89ab-cdef\njeronimo\n_\n"
            "plain\njeronimo\njeronimo\n_\n"
            "plain\njob:job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob-0123-cdef\n_\n_\n"
            "plain\njob:job-0123-cdef\n_\n_\n"
            "plain\njob:/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob-89ab-4567\n_\n_\n"
            "plain\njob:job-89ab-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_\n"
            "plain\njob://other-cluster/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "jo"])
        assert bash_out == (
            "plain,job-0123-4567,\n"
            "plain,job:job-0123-4567,\n"
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job-89ab-cdef,\n"
            "plain,job:job-89ab-cdef,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job-0123-cdef,\n"
            "plain,job:job-0123-cdef,\n"
            "plain,job:/other-user/job-0123-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,\n"
            "plain,job-89ab-4567,\n"
            "plain,job:job-89ab-4567,\n"
            "plain,job:/test-user/job-89ab-4567,\n"
            "plain,job://other-cluster/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob-0123-4567\n_\n_\n"
            "plain\njob:job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob-89ab-cdef\njeronimo\n_\n"
            "plain\njob:job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob-0123-cdef\n_\n_\n"
            "plain\njob:job-0123-cdef\n_\n_\n"
            "plain\njob:/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob-89ab-4567\n_\n_\n"
            "plain\njob:job-89ab-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_\n"
            "plain\njob://other-cluster/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "je"])
        assert bash_out == "plain,jeronimo,"
        assert zsh_out == "plain\njeronimo\njeronimo\n_"

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:"])
        assert bash_out == (
            "plain,job:job-0123-4567,\n"
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job:job-89ab-cdef,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job:job-0123-cdef,\n"
            "plain,job:/other-user/job-0123-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,\n"
            "plain,job:job-89ab-4567,\n"
            "plain,job:/test-user/job-89ab-4567,\n"
            "plain,job://other-cluster/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob:job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob:job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:job-0123-cdef\n_\n_\n"
            "plain\njob:/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob:job-89ab-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_\n"
            "plain\njob://other-cluster/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:j"])
        assert bash_out == (
            "plain,job:job-0123-4567,\n"
            "plain,job:job-89ab-cdef,\n"
            "plain,job:job-0123-cdef,\n"
            "plain,job:job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob:job-0123-4567\n_\n_\n"
            "plain\njob:job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:job-0123-cdef\n_\n_\n"
            "plain\njob:job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:je"])
        assert bash_out == ""
        assert zsh_out == ""

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:/"])
        assert bash_out == (
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job:/other-user/job-0123-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,\n"
            "plain,job:/test-user/job-89ab-4567,\n"
            "plain,job://other-cluster/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_\n"
            "plain\njob://other-cluster/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:/t"])
        assert bash_out == (
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job:/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job:/test-user/j"])
        assert bash_out == (
            "plain,job:/test-user/job-0123-4567,\n"
            "plain,job:/test-user/job-89ab-cdef,\n"
            "plain,job:/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob:/test-user/job-0123-4567\n_\n_\n"
            "plain\njob:/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob:/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job://"])
        assert bash_out == (
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,\n"
            "plain,job://other-cluster/test-user/job-89ab-4567,"
        )
        assert zsh_out == (
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_\n"
            "plain\njob://other-cluster/test-user/job-89ab-4567\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job://d"])
        assert bash_out == (
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,"
        )
        assert zsh_out == (
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_"
        )

        zsh_out, bash_out = run_autocomplete(["job", "status", "job://default/"])
        assert bash_out == (
            "plain,job://default/test-user/job-0123-4567,\n"
            "plain,job://default/test-user/job-89ab-cdef,\n"
            "plain,job://default/other-user/job-0123-cdef,"
        )
        assert zsh_out == (
            "plain\njob://default/test-user/job-0123-4567\n_\n_\n"
            "plain\njob://default/test-user/job-89ab-cdef\njeronimo\n_\n"
            "plain\njob://default/other-user/job-0123-cdef\n_\n_"
        )
