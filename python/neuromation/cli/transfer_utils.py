import asyncio
import logging
import pathlib
from typing import AsyncIterator

from yarl import URL

from neuromation.clientv2 import ClientV2, ResourceNotFound

from .command_progress_report import ProgressBase


log = logging.getLogger(__name__)


async def _iterate_file(
    progress: ProgressBase, src: pathlib.Path
) -> AsyncIterator[bytes]:
    loop = asyncio.get_event_loop()
    progress.start(str(src), src.stat().st_size)
    with src.open("rb") as stream:
        chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
        pos = len(chunk)
        while chunk:
            progress.progress(str(src), pos)
            yield chunk
            chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
            pos += len(chunk)
        progress.complete(str(src))


async def upload_file(
    client: ClientV2, progress: ProgressBase, src: URL, dst: URL
) -> None:
    src = client.storage.normalize_local(src)
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if path.is_dir():
        raise IsADirectoryError(f"{path} is a directory, use recursive copy")
    if not path.is_file():
        raise OSError(f"{path} should be a regular file")
    dst = client.storage.normalize(dst)
    if not dst.name:
        # file:src/file.txt -> storage:dst/ ==> storage:dst/file.txt
        dst = dst / src.name
    await client.storage.create(dst, _iterate_file(progress, path))


async def upload_dir(
    client: ClientV2, progress: ProgressBase, src: URL, dst: URL
) -> None:
    src = client.storage.normalize_local(src)
    dst = client.storage.normalize(dst)
    if not dst.name:
        # /dst/ ==> /dst for recursive copy
        dst = dst.parent
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"{path} should be a directory")
    try:
        stat = await client.storage.stats(dst)
        if not stat.is_dir():
            raise NotADirectoryError(f"{dst} should be a directory")
    except ResourceNotFound:
        await client.storage.mkdirs(dst)
    for child in path.iterdir():
        if child.is_file():
            await upload_file(client, progress, src / child.name, dst / child.name)
        elif child.is_dir():
            await upload_dir(client, progress, src / child.name, dst / child.name)
        else:
            log.warning("Cannot upload %s", child)


async def download_file(
    client: ClientV2, progress: ProgressBase, src: URL, dst: URL
) -> None:
    loop = asyncio.get_event_loop()
    src = client.storage.normalize(src)
    dst = client.storage.normalize_local(dst)
    path = pathlib.Path(dst.path).resolve(True)
    if path.exists():
        if path.is_dir():
            path = path / src.name
        elif not path.is_file():
            raise OSError(f"{path} should be a regular file")
    if not path.name:
        # storage:src/file.txt -> file:dst/ ==> file:dst/file.txt
        path = path / src.name
    with path.open("wb") as stream:
        size = 0  # TODO: display length hint for downloaded file
        progress.start(str(dst), size)
        pos = 0
        async for chunk in client.storage.open(src):
            pos += len(chunk)
            progress.progress(str(dst), pos)
            loop.run_in_executor(None, stream.write(chunk))
        progress.complete(str(dst))


async def download_dir(
    client: ClientV2, progress: ProgressBase, src: URL, dst: URL
) -> None:
    src = client.storage.normalize(src)
    dst = client.storage.normalize_local(dst)
    if not dst.name:
        # /dst/ ==> /dst for recursive copy
        dst = dst.parent
    path = pathlib.Path(dst.path).resolve(True)
    path.mkdir(parents=True, exist_ok=True)
    for child in await client.ls(src):
        if child.is_file():
            await download_file(client, progress, src / child.name, dst / child.name)
        elif child.is_dir():
            await download_dir(client, progress, src / child.name, dst / child.name)
        else:
            log.warning("Cannot upload %s", child)


async def copy(
    client: ClientV2, progress: ProgressBase, recursive: bool, src: URL, dst: URL
):
    if not src.scheme:
        src = src.with_scheme("storage")
    if not dst.scheme:
        dst = dst.with_scheme("storage")
    if src.scheme == "file" and dst.scheme == "storage":
        if recursive:
            await upload_dir(client, progress, src, dst)
        else:
            await upload_file(client, progress, src, dst)
    elif src.scheme == "storage" and dst.scheme == "file":
        if recursive:
            await download_dir(client, progress, src, dst)
        else:
            await download_file(client, progress, src, dst)
    else:
        raise RuntimeError(f"Copy operation for {src} -> {dst} is not supported")
