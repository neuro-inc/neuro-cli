import asyncio
import pathlib
from typing import AsyncIterator

from yarl import URL

from neuromation.clientv2 import ClientV2

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
    client: ClientV2, src: URL, dst: URL, progress: ProgressBase
) -> None:
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_file():
        raise IsADirectoryError(f"{path} should be a regular file")
    await client.storage.create(dst, _iterate_file(progress, path))


async def upload_dir(
    client: ClientV2, src: URL, dst: URL, progress: ProgressBase
) -> None:
    path = pathlib.Path(src.path).resolve(True)
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    if not path.is_file():
        raise IsADirectoryError(f"{path} should be a regular file")
    await client.storage.create(dst, _iterate_file(progress, path))
