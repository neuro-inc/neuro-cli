import abc
import logging
import os
import tarfile
from os.path import dirname
from typing import Callable, List
from urllib.parse import ParseResult

import aiofiles

from neuromation.client import FileStatus

log = logging.getLogger(__name__)


BUFFER_SIZE_MB = 16

PLATFORM_DELIMITER = '/'


SYSTEM_PATH_DELIMITER = os.sep


class PlatformMakeDirOperation:

    def mkdir(self, path: str, storage: Callable):
        with storage() as s:
            return s.mkdirs(path=path)


class PlatformListDirOperation:

    def ls(self, path: str, storage: Callable):
        with storage() as s:
            return s.ls(path=path)


class CopyOperation:

    @abc.abstractmethod
    def _copy(self, src: str, dst: str,
              storage: Callable):   # pragma: no cover
        pass

    def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        self._copy(src.path, dst.path, storage)
        return dst.geturl()

    @classmethod
    def create(cls, src_scheme: str, dst_scheme: str,
               recursive: bool) -> 'CopyOperation':
        if src_scheme == 'file':
            if dst_scheme == 'storage':
                if recursive:
                    return RecursiveLocalToPlatformV2()
                else:
                    return NonRecursiveLocalToPlatform()
            else:
                raise ValueError('storage:// and file:// schemes required')
        elif src_scheme == 'storage':
            if dst_scheme == 'file':
                if recursive:
                    return RecursivePlatformToLocal()
                else:
                    return NonRecursivePlatformToLocal()
            else:
                raise ValueError('storage:// and file:// schemes required')
        raise ValueError('storage:// and file:// schemes required')


class NonRecursivePlatformToLocal(CopyOperation):

    def transfer(self, i, o):  # pragma: no cover
        log.debug(f'Input: {i}')
        log.debug(f'Output: {o}')

        while True:
            buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

            if not buf:
                break

            o.write(buf)

    def _copy(self, src: str, dst: str,
              storage: Callable):   # pragma: no cover
        return self.copy_file(src, dst, storage)

    def copy_file(self, src, dst, storage):  # pragma: no cover
        with storage() as s:
            with s.open(path=src) as stream:
                with open(dst, mode='wb') as f:
                    self.transfer(stream, f)
                    return None

    def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        platform_file_name = src.path.split(PLATFORM_DELIMITER)[-1]
        platform_file_path = dirname(src.path)

        # define local
        if os.path.exists(dst.path) and os.path.isdir(dst.path):
                #         get file name from src
                dst_path = os.path.join(dst.path, platform_file_name)
        else:
            if dst.path.endswith(SYSTEM_PATH_DELIMITER):
                raise ValueError('Target should exist. '
                                 'Please create directory, '
                                 'or point to existing file.')

            try_dir = dirname(dst.path)
            if not os.path.isdir(try_dir):
                raise ValueError('Target should exist. '
                                 'Please create directory, '
                                 'or point to existing file.')
            dst_path = dst.path.rstrip(SYSTEM_PATH_DELIMITER)

        # check remote
        files = PlatformListDirOperation().ls(platform_file_path, storage)
        try:
            next(file
                 for file in files
                 if file.path == platform_file_name and file.type == 'FILE')
        except StopIteration as e:
            raise ValueError('Source file not found.') from e

        self._copy(src.path, dst_path, storage)
        return dst.geturl()


class RecursivePlatformToLocal(NonRecursivePlatformToLocal):

    def _copy(self, src: str, dst: str, storage: Callable):
        files: List[FileStatus] = PlatformListDirOperation()\
            .ls(path=src, storage=storage)
        for file in files:
            name = file.path
            target = os.path.join(dst, name)
            if file.type == 'DIRECTORY':
                os.mkdir(target)
                self._copy(src + '/' + name, target, storage)
            else:
                self.copy_file(f'{src}{PLATFORM_DELIMITER}{name}',
                               target, storage)
        return dst

    def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(dst.path):
            raise ValueError('Target should exist. '
                             'Please create targert directory and try again.')

        if not os.path.isdir(dst.path):
            raise ValueError('Target should be directory. '
                             'Please correct your command line arguments.')

        src_path = src.path.rstrip(PLATFORM_DELIMITER)
        dest_path = dst.path.rstrip('/')

        # check remote
        platform_file_name = src_path.split(PLATFORM_DELIMITER)[-1]
        platform_file_path = dirname(src_path)

        files = PlatformListDirOperation().ls(platform_file_path, storage)
        try:
            next(file
                 for file in files
                 if file.path == platform_file_name
                 and file.type == 'DIRECTORY')
        except StopIteration as e:
            raise ValueError('Source directory not found.') from e

        self._copy(src_path, dest_path, storage)
        return dst.geturl()


class NonRecursiveLocalToPlatform(CopyOperation):

    def copy_file(self, src_path: str, dest_path: str,
                  storage: Callable):   # pragma: no cover
        # TODO (R Zubairov 09/19/18) Check with Andrey if there any way
        # to track progress and report
        with open(src_path, mode='rb') as f:
            with storage() as s:
                s.create(path=dest_path, data=f)
                return dest_path

    def _copy(self, src: str, dst: str, storage: Callable):
        log.debug(f'Copy {src} to {dst}.')
        return self.copy_file(src, dst, storage)


class RecursiveLocalToPlatform(NonRecursiveLocalToPlatform):

    async def copy_single_file(self):
        copy it

    async def _copy(self, src: str, dst: str, storage: Callable):
        # TODO should we create directory by default - root
        dst = dst.rstrip(PLATFORM_DELIMITER)
        dst = f'{dst}{PLATFORM_DELIMITER}'
        for root, subdirs, files in os.walk(src):
            if root != src:
                suffix_path = os.path.relpath(root, src)
                pref_path = f'{dst}{suffix_path}{PLATFORM_DELIMITER}'
            else:
                suffix_path = ''
                pref_path = dst
            for file in files:
                target_dest = f'{pref_path}{file}'
                src_file = os.path.join(root, file)
                self.copy_file(src_file, target_dest, storage)

                for file from batch_of_files:
                    coroutine = self.copy_file()

                wait for all

            for subdir in subdirs:
                target_dest = f'{pref_path}{subdir}'
                PlatformMakeDirOperation().mkdir(target_dest, storage)


class RecursiveLocalToPlatformV2(NonRecursiveLocalToPlatform):
    """Tar base copying process"""

    READ_CHUNK_SIZE = 64 * 1024

    async def file_sender(self, src: str, total_size: int, files: List):
        for file in files:
            file_name = file['name']
            stat = file['stat']
            print(file_name, end='\r')

            # stat = await self.io_stat(src + file_name)
            tar_info = tarfile.TarInfo(name=file_name)
            tar_info.mtime = stat.st_mtime
            tar_info.mode = stat.st_mode

            if stat.S_ISDIR(stat.st_mode):
                tar_info.type = tarfile.DIRTYPE
                yield tar_info.tobuf(tarfile.GNU_FORMAT, "utf-8", 'surrogateescape')
            elif stat.S_ISREG(stat.st_mode):
                tar_info.type = tarfile.REGTYPE
                tar_info.size = stat.st_size
                yield tar_info.tobuf(tarfile.GNU_FORMAT, "utf-8", 'surrogateescape')
                # TODO line below is completelly broken
                async with aiofiles.open(src + file_name, 'rb') as f:
                    chunk = await f.read(self.READ_CHUNK_SIZE)
                    while chunk:
                        yield chunk
                        chunk = await f.read(self.READ_CHUNK_SIZE)
                blocks, remainder = divmod(tar_info.size, tarfile.BLOCKSIZE)
                if remainder:
                    yield tarfile.NUL * (tarfile.BLOCKSIZE - remainder)
            print('                                                                    ', end='\r')

    def _copy(self, src: str, dst: str, storage: Callable):
        # TODO should we create directory by default - root
        dst = dst.rstrip(PLATFORM_DELIMITER)
        dst = f'{dst}{PLATFORM_DELIMITER}'
        rfiles = []
        total_size = 0
        for root, subdirs, files in os.walk(src):
            if root != src:
                suffix_path = os.path.relpath(root, src)
                pref_path = f'{suffix_path}{PLATFORM_DELIMITER}'
            else:
                pref_path = ''

            for subdir in subdirs:
                target_dest = f'{pref_path}{subdir}'
                os_stat = os.stat(src + '/' + target_dest)
                rfiles.append({'name': target_dest, 'stat:': os_stat})
            for file in files:
                target_dest = f'{pref_path}{file}'
                os_stat = os.stat(src + '/' + target_dest)
                total_size += os_stat.st_size
                rfiles.append({'name': target_dest, 'stat:': os_stat})

        with storage() as s:
            s.create_archived_on_fly(path=dst, data=self.file_sender(src + '/', total_size=total_size, files=rfiles))
            return dst
