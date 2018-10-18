import abc
import logging
import os
from os.path import dirname
from pathlib import Path, PosixPath, PurePath
from typing import Callable, Dict, List, Optional
from urllib.parse import ParseResult, urlparse

from neuromation import Resources
from neuromation.client import FileStatus, Image, ResourceNotFound
from neuromation.client.jobs import NetworkPortForwarding

log = logging.getLogger(__name__)

BUFFER_SIZE_MB = 16

PLATFORM_DELIMITER = '/'

SYSTEM_PATH_DELIMITER = os.sep


class PlatformStorageOperation:

    def __init__(self, principal: str):
        self.principal = principal

    def _get_principal(self, path_url: ParseResult) -> str:
        path_principal = path_url.netloc
        if not path_principal:
            path_principal = self.principal
        if path_principal == '~':
            path_principal = self.principal
        return path_principal

    def _is_storage_path_url(self, path: ParseResult):
        if path.scheme != 'storage':
            raise ValueError('Path should be targeting platform storage.')

    def _render_platform_path(self, path_str: str) -> PosixPath:
        target_path: PosixPath = PosixPath(path_str)
        if target_path.is_absolute():
            target_path = target_path.relative_to(PosixPath('/'))
        return target_path

    def _render_platform_path_with_principal(self,
                                             path: ParseResult) -> PosixPath:
        target_path: PosixPath = self._render_platform_path(path.path)
        target_principal = self._get_principal(path)
        return PosixPath(PLATFORM_DELIMITER, target_principal, target_path)

    def _get_parent(self, path: PosixPath) -> PosixPath:
        return path.parent

    def render_uri_path_with_principal(self, path: str):
        path_url = urlparse(path, scheme='file')
        self._is_storage_path_url(path_url)
        return self._render_platform_path_with_principal(path_url)


class PlatformMakeDirOperation(PlatformStorageOperation):

    def mkdir(self, path_str: str, storage: Callable):
        final_path = self.render_uri_path_with_principal(path_str)
        # TODO CHECK parent exists
        with storage() as s:
            return s.mkdirs(path=str(final_path))


class PlatformListDirOperation(PlatformStorageOperation):

    def ls(self, path_str: str, storage: Callable):
        final_path = self.render_uri_path_with_principal(path_str)
        with storage() as s:
            return s.ls(path=str(final_path))


class PlatformRemoveOperation(PlatformStorageOperation):

    def remove(self, path_str: str, storage: Callable):
        path = urlparse(path_str, scheme='file')
        self._is_storage_path_url(path)
        final_path = self._render_platform_path_with_principal(path)

        # TODO test how it will work on Windows Platform
        # Lets protect user against typos in command line
        # We can of course ask user whether he really wants
        # to delete every file. Yet it is going to be nightmare
        # in case of REST
        target_path: PosixPath = self._render_platform_path(path.path)
        if str(target_path) == '.':
            raise ValueError('Invalid path value.')
        with storage() as s:
            return s.rm(path=str(final_path))


class CopyOperation(PlatformStorageOperation):

    @abc.abstractmethod
    def _copy(self, src: ParseResult, dst: ParseResult,
              storage: Callable):  # pragma: no cover
        pass

    def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        log.debug(f'Copy {src} to {dst}.')
        copy_result = self._copy(src, dst, storage)
        return copy_result

    def _ls(self, path: str, storage: Callable):
        ls = PlatformListDirOperation(self.principal)
        return ls.ls(f'storage:/{path}', storage)

    @classmethod
    def create(cls, principal: str, src_scheme: str, dst_scheme: str,
               recursive: bool) -> 'CopyOperation':
        if src_scheme == 'file':
            if dst_scheme == 'storage':
                if recursive:
                    return RecursiveLocalToPlatform(principal)
                else:
                    return NonRecursiveLocalToPlatform(principal)
            else:
                raise ValueError(
                    'storage:// and file:// schemes required')
        elif src_scheme == 'storage':
            if dst_scheme == 'file':
                if recursive:
                    return RecursivePlatformToLocal(principal)
                else:
                    return NonRecursivePlatformToLocal(principal)
            else:
                raise ValueError(
                    'storage:// and file:// schemes required')
        raise ValueError(
            'storage:// and file:// schemes required')


class NonRecursivePlatformToLocal(CopyOperation):

    def transfer(self, i, o):  # pragma: no cover
        log.debug(f'Input: {i}')
        log.debug(f'Output: {o}')

        while True:
            buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

            if not buf:
                break

            o.write(buf)

    def copy_file(self, src: str, dst: str, storage):  # pragma: no cover
        with storage() as s:
            with s.open(path=src) as stream:
                with open(dst, mode='wb') as f:
                    self.transfer(stream, f)
                    return dst

    def _copy(self, src: ParseResult, dst: ParseResult,
              storage: Callable):  # pragma: no cover
        platform_file_name = self._render_platform_path_with_principal(src)

        # define local
        if os.path.exists(dst.path) and os.path.isdir(dst.path):
            #         get file name from src
            dst_path = Path(dst.path, platform_file_name.name)
        else:
            if dst.path.endswith(SYSTEM_PATH_DELIMITER):
                raise NotADirectoryError('Target should exist. '
                                         'Please create directory, '
                                         'or point to existing file.')

            try_dir = dirname(dst.path)
            if try_dir != '' and not os.path.isdir(try_dir):
                raise FileNotFoundError('Target should exist. '
                                        'Please create directory, '
                                        'or point to existing file.')
            dst_path = Path(dst.path)

        # check remote
        files = self._ls(str(platform_file_name.parent), storage)
        try:
            next(file
                 for file in files
                 if file.path == platform_file_name.name
                 and file.type == 'FILE')
        except StopIteration as e:
            raise ResourceNotFound(f'Source file {src.path} not found.') from e

        copy_file = self.copy_file(str(platform_file_name),
                                   str(dst_path),
                                   storage)
        return copy_file


class RecursivePlatformToLocal(NonRecursivePlatformToLocal):

    def _copy_obj(self, src: PosixPath, dst: Path, storage: Callable):
        files: List[FileStatus] = PlatformListDirOperation(self.principal) \
            .ls(path_str=f'storage:/{src}', storage=storage)

        for file in files:
            name = file.path
            target = Path(dst, name)
            if file.type == 'DIRECTORY':
                os.mkdir(target)
                self._copy_obj(PosixPath(src, name), target, storage)
            else:
                platform_file_name = f'{src}{PLATFORM_DELIMITER}{name}'
                self.copy_file(platform_file_name, str(target), storage)

    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(dst.path):
            raise FileNotFoundError('Target should exist. '
                                    'Please create target directory '
                                    'and try again.')

        if not os.path.isdir(dst.path):
            raise NotADirectoryError('Target should be directory. '
                                     'Please correct your '
                                     'command line arguments.')

        # Test that source directory exists.
        platform_file_name = self._render_platform_path_with_principal(src)
        platform_file_path = self._get_parent(platform_file_name)
        # TODO here we should have work around when someone
        # tries to copy full directory of a person
        if str(platform_file_path) != '/':
            files = self._ls(str(platform_file_path), storage)
            try:
                next(file
                     for file in files
                     if file.path == str(platform_file_name.name)
                     and file.type == 'DIRECTORY')
            except StopIteration as e:
                raise ResourceNotFound('Source directory not found.') from e

        self._copy_obj(platform_file_name, Path(dst.path), storage)

        return dst


class NonRecursiveLocalToPlatform(CopyOperation):

    def _is_dir_on_platform(self, path: PosixPath, storage: Callable) -> bool:
        """Tests whether specified path is directory on a platform or not.
        Test is done by running LS command.
        """
        try:
            self._ls(str(path), storage)
        except ResourceNotFound as e:
            return False
        return True

    def copy_file(self, src_path: str, dest_path: str,
                  storage: Callable):  # pragma: no cover
        # TODO (R Zubairov 09/19/18) Check with Andrey if there any way
        # to track progress and report
        with open(src_path, mode='rb') as f:
            with storage() as s:
                s.create(path=dest_path, data=f)
                return dest_path

    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise FileNotFoundError('Source file not found.')

        if os.path.isdir(src.path):
            raise IsADirectoryError('Source should be file.')

        target_path: PosixPath = self._render_platform_path_with_principal(dst)
        target_dir_not_exists = 'Target directory does not exist.'
        if len(dst.path) and dst.path[-1] == PLATFORM_DELIMITER:
            if not self._is_dir_on_platform(target_path, storage):
                raise NotADirectoryError(target_dir_not_exists)
            target_path = PosixPath(target_path, Path(src.path).name)
        else:
            if not self._is_dir_on_platform(target_path, storage):
                if not self._is_dir_on_platform(target_path.parent, storage):
                    raise NotADirectoryError(target_dir_not_exists)
            else:
                target_path = PosixPath(target_path, Path(src.path).name)

        copy_file = self.copy_file(src.path, str(target_path), storage)
        return f'storage:/{copy_file}'


class RecursiveLocalToPlatform(NonRecursiveLocalToPlatform):

    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise ValueError('Source should exist.')

        if not os.path.isdir(src.path):
            return NonRecursiveLocalToPlatform._copy(self,
                                                     src,
                                                     dst,
                                                     storage)

        final_path = self._render_platform_path_with_principal(dst)
        src_dir_path = PurePath(src.path).name
        if src_dir_path != '':
            final_path = PosixPath(final_path, src_dir_path)

        for root, subdirs, files in os.walk(src.path):
            if root != src.path:
                suffix_path = os.path.relpath(root, src.path)
                pref_path = f'{final_path}{PLATFORM_DELIMITER}' \
                            f'{suffix_path}{PLATFORM_DELIMITER}'
            else:
                suffix_path = ''
                pref_path = f'{final_path}{PLATFORM_DELIMITER}'
            for file in files:
                target_dest = f'{pref_path}{file}'
                src_file = os.path.join(root, file)
                self.copy_file(src_file, target_dest, storage)
            for subdir in subdirs:
                target_dest = f'{pref_path}{subdir}'
                PlatformMakeDirOperation(self.principal).mkdir(
                    f'storage:/{target_dest}',
                    storage)
        return final_path


class ModelHandlerOperations(PlatformStorageOperation):
    def train(self, image, dataset, results,
              gpu, cpu, memory, extshm,
              cmd, model, http, ssh):
        try:
            dataset_platform_path = self.render_uri_path_with_principal(
                dataset)
        except ValueError as e:
            raise ValueError('Dataset path should be on platform. '
                             'Specify scheme storage:')

        try:
            resultset_platform_path = self.render_uri_path_with_principal(
                results)
        except ValueError as e:
            raise ValueError('Results path should be on platform. '
                             'Specify scheme storage:')

        net = None
        ports: Dict[str, int] = {}
        if http:
            ports['http'] = http
        if ssh:
            ports['ssh'] = ssh
        if ports:
            net = NetworkPortForwarding(ports)

        cmd = ' '.join(cmd) if cmd is not None else None
        log.debug(f'cmd="{cmd}"')

        cpu = float(cpu)
        gpu = int(gpu)
        extshm = bool(extshm)

        with model() as m:
            job = m.train(
                image=Image(
                    image=image,
                    command=cmd),
                network=net,
                resources=Resources(
                    memory=memory,
                    gpu=gpu,
                    cpu=cpu,
                    shm=extshm
                ),
                dataset=f'storage:/{dataset_platform_path}',
                results=f'storage:/{resultset_platform_path}')

        return job


class JobHandlerOperations():

    def list_jobs(self, status: Optional[str], jobs: Callable) -> str:
        def short_format(item) -> str:
            image = item.image if item.image else ''
            command = item.command if item.command else ''
            return f'{item.id}' \
                   f'    {item.status:<10}' \
                   f'    {image:<25}' \
                   f'    {command}'

        with jobs() as j:
            return '\n'.join([
                short_format(item)
                for item in
                j.list()
                if not status or item.status == status
            ])
