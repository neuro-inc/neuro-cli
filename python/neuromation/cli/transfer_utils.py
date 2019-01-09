import asyncio
import logging
import pathlib
from typing import AsyncIterator

from yarl import URL

from neuromation.clientv2 import ClientV2, FileStatusType, ResourceNotFound

from .command_progress_report import ProgressBase


log = logging.getLogger(__name__)


async def _iterate_file(
    progress: ProgressBase, src: pathlib.Path
) -> AsyncIterator[bytes]:
    loop = asyncio.get_event_loop()
    stat = await loop.run_in_executor(None, src.stat)
    progress.start(str(src), stat.st_size)
    stream = await loop.run_in_executor(None, src.open, "rb")
    try:
        chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
        pos = len(chunk)
        while chunk:
            progress.progress(str(src), pos)
            chunk = await loop.run_in_executor(None, stream.read, 1024 * 1024)
            pos += len(chunk)
            yield chunk
        progress.complete(str(src))
    finally:
        await loop.run_in_executor(None, stream.close)


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
        # file:src/file.txt -> storage:dst/ ==> sotrage:dst/file.txt
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
        if not stat.type == FileStatusType.DIRECTORY:
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


async def copy(
    client: ClientV2, progress: ProgressBase, recursive: bool, src: URL, dst: URL
):
    if src.scheme == "file" and dst.scheme == "storage":
        if recursive:
            await upload_dir(client, progress, src, dst)
        else:
            await upload_file(client, progress, src, dst)
    else:
        raise RuntimeError(f"Copy operation for {src} -> {dst} is not supported")
