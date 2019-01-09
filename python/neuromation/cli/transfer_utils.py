import asyncio
import pathlib
from http import HTTPStatus
from typing import AsyncIterator

import aiohttp
from yarl import URL

from neuromation.clientv2 import ClientV2, FileStatusType

from .command_progress_report import ProgressBase


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
    src = client.storage.normalize(src)
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_file():
        raise IsADirectoryError(f"{path} should be a regular file")
    dst = client.storage.normalize(dst)
    if not dst.name:
        dst = dst / src.name
    await client.storage.create(dst, _iterate_file(progress, path))


async def upload_dir(
    client: ClientV2, progress: ProgressBase, src: URL, dst: URL
) -> None:
    src = client.storage.normalize(src)
    dst = client.storage.normalize(dst)
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_dir():
        raise NotADirectoryError(f"{path} should be a directory")
    try:
        stat = await client.storage.stats(dst)
        if not stat.type == FileStatusType.DIRECTORY:
            raise NotADirectoryError(f"{dst} should be a directory")
    except aiohttp.ClientResponseError as ex:
        if ex.status != HTTPStatus.NOT_FOUND:
            raise
        await client.storage.mkdirs(dst)
    for child in path.iterdir():
        
    await client.storage.create(dst, _iterate_file(progress, path))
