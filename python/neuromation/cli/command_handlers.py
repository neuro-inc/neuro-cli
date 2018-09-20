import abc
import logging
import os
from typing import Callable, List, Optional
from urllib.parse import ParseResult

from neuromation.client import FileStatus

log = logging.getLogger(__name__)


BUFFER_SIZE_MB = 16

PLATFORM_DELIMITER = '/'


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
               recursive: bool) -> Optional['CopyOperation']:
        if src_scheme == 'file':
            if dst_scheme == 'storage':
                if recursive:
                    return RecursiveLocalToPlatform()
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
        return None


class NonRecursivePlatformToLocal(CopyOperation):

    def transfer(self, i, o):
        log.debug(f'Input: {i}')
        log.debug(f'Output: {o}')

        while True:
            buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

            if not buf:
                break

            o.write(buf)

    def _copy(self, src: str, dst: str, storage: Callable):
        return self.copy_file(dst, src, storage)

    def copy_file(self, dst, src, storage):
        with storage() as s:
            with s.open(path=src) as stream:
                with open(dst, mode='wb') as f:
                    self.transfer(stream, f)
                    return None


class RecursivePlatformToLocal(NonRecursivePlatformToLocal):

    def _copy(self, src: str, dst: str, storage: Callable):
        files: List[FileStatus] = PlatformListDirOperation()\
            .ls(path=src, storage=storage)
        for file in files:
            name = file.path
            target = os.path.join(dst, name)
            if file.type == 'directory':
                os.mkdir(target)
                self.copy(src + '/' + name, target, storage)
            else:
                self.copy_file(f'{src}{PLATFORM_DELIMITER}{name}',
                               target, storage)
        return dst


class NonRecursiveLocalToPlatform(CopyOperation):

    def copy_file(self, src_path: str, dest_path: str, storage: Callable):
        # TODO (R Zubairov 09/19/18) Check with Andrey if there any way
        # to track progress and report
        with open(src_path, mode='rb') as f:
            with storage() as s:
                s.create(path=dest_path, data=f)
                return dest_path

    @abc.abstractmethod
    def _copy(self, src: str, dst: str, storage: Callable):
        log.debug(f'Copy {src} to {dst}.')
        return self.copy_file(src, dst, storage)


class RecursiveLocalToPlatform(NonRecursiveLocalToPlatform):

    @abc.abstractmethod
    def _copy(self, src: str, dst: str, storage: Callable):
        # TODO should we create directory by default - root
        for root, subdirs, files in os.walk(src):
            log.debug(f'{len(files)} {src}')
            for file in files:
                target_dest = f'{dst}{self.PLATFORM_DELIMITER}{file}'
                src_file = os.path.join(root, file)
                self.copy_file(src_file, target_dest, storage)
            for subdir in subdirs:
                src_file = os.path.join(root, subdir)
                target_dest = f'{dst}{self.PLATFORM_DELIMITER}{subdir}'
                PlatformMakeDirOperation().mkdir(target_dest, storage)
                self.copy(src_file, target_dest, storage)
