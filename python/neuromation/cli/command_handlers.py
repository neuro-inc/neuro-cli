import abc
import logging
import os
from os.path import dirname
from pathlib import Path, PosixPath, PurePath, PurePosixPath
from typing import Callable, Dict, List, Optional
from urllib.parse import ParseResult, urlparse

import docker
from docker.errors import APIError

from neuromation.cli.command_progress_report import ProgressBase
from neuromation.client import FileStatus, ResourceNotFound


log = logging.getLogger(__name__)

BUFFER_SIZE_MB = 1

BUFFER_SIZE_B = BUFFER_SIZE_MB * 1024 * 1024

PLATFORM_DELIMITER = "/"

SYSTEM_PATH_DELIMITER = os.sep


class PlatformOperation:
    def __init__(self, principal: str, token: str) -> None:
        self._principal = principal
        self._token = token


class PlatformStorageOperation:
    def __init__(self, principal: str):
        self.principal = principal

    def _get_principal(self, path_url: ParseResult) -> str:
        path_principal = path_url.hostname
        if not path_principal:
            path_principal = self.principal
        if path_principal == "~":
            path_principal = self.principal
        return path_principal

    def _is_storage_path_url(self, path: ParseResult):
        if path.scheme != "storage":
            raise ValueError("Path should be targeting platform storage.")

    def _render_platform_path(self, path_str: str) -> PosixPath:
        target_path: PosixPath = PosixPath(path_str)
        if target_path.is_absolute():
            target_path = target_path.relative_to(PosixPath("/"))
        return target_path

    def _render_platform_path_with_principal(self, path: ParseResult) -> PosixPath:
        target_path: PosixPath = self._render_platform_path(path.path)
        target_principal = self._get_principal(path)
        posix_path = PurePosixPath(PLATFORM_DELIMITER, target_principal, target_path)
        return posix_path

    def render_uri_path_with_principal(self, path: str):
        # Special case that shall be handled here, when path is '//'
        if path == "storage://":
            return PosixPath(PLATFORM_DELIMITER)

        # Normal processing flow
        path_url = urlparse(path, scheme="file")
        self._is_storage_path_url(path_url)
        return self._render_platform_path_with_principal(path_url)


class PlatformSharingOperations(PlatformStorageOperation):
    def share(self, path_str: str, op_type: str, whom: str, resource_sharing: Callable):
        what = urlparse(path_str, scheme="file")
        target_platform_path = self._render_platform_path_with_principal(what)
        with resource_sharing() as rs:
            resource_uri = f"{what.scheme}:/{target_platform_path}"
            return rs.share(resource_uri, op_type, whom)


class PlatformMakeDirOperation(PlatformStorageOperation):
    def mkdir(self, path_str: str, storage: Callable):
        final_path = self.render_uri_path_with_principal(path_str)
        # TODO CHECK parent exists
        with storage() as s:
            return s.mkdirs(path=str(final_path))


class PlatformListDirOperation(PlatformStorageOperation):
    def ls(self, path_str: str, storage: Callable) -> List[FileStatus]:
        final_path = self.render_uri_path_with_principal(path_str)
        with storage() as s:
            return s.ls(path=str(final_path))


class PlatformRemoveOperation(PlatformStorageOperation):
    def remove(self, path_str: str, storage: Callable):
        path = urlparse(path_str, scheme="file")
        self._is_storage_path_url(path)
        final_path = self.render_uri_path_with_principal(path_str)

        root_data_path = PosixPath("/")

        # Minor protection against deleting everything from root
        # or user volume root, however force operation here should
        # allow user to delete everything
        if final_path == root_data_path or final_path.parent == root_data_path:
            raise ValueError("Invalid path value.")

        with storage() as s:
            return s.rm(path=str(final_path))


class PlatformRenameOperation(PlatformStorageOperation):
    def mv(self, src_str: str, dst_str: str, storage: Callable):
        src_path_str = str(self.render_uri_path_with_principal(src_str))
        dst_path_str = str(self.render_uri_path_with_principal(dst_str))
        with storage() as s:
            return s.mv(src_path=src_path_str, dst_path=dst_path_str)


class CopyOperation(PlatformStorageOperation):
    def __init__(self, principal: str, progress: ProgressBase):
        super().__init__(principal)
        self.progress = progress

    def _file_stat_on_platform(
        self, path: PosixPath, storage: Callable
    ) -> Optional[FileStatus]:
        try:
            with storage() as s:
                file_status = s.stats(path=str(path))
                return file_status
        except ResourceNotFound:
            return None

    def _is_dir_on_platform(self, path: PosixPath, storage: Callable) -> bool:
        """Tests whether specified path is directory on a platform or not."""
        platform = self._file_stat_on_platform(path, storage)
        if platform:
            return platform.type == "DIRECTORY"
        return False

    @abc.abstractmethod
    def _copy(
        self, src: ParseResult, dst: ParseResult, storage: Callable
    ):  # pragma: no cover
        pass

    def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        log.debug(f"Copy {src} to {dst}.")
        copy_result = self._copy(src, dst, storage)
        return copy_result

    @classmethod
    def create(
        cls,
        principal: str,
        src_scheme: str,
        dst_scheme: str,
        recursive: bool,
        progress_enabled: bool = False,
    ) -> "CopyOperation":
        log.debug(f"p = {progress_enabled}")
        progress: ProgressBase = ProgressBase.create_progress(progress_enabled)
        if src_scheme == "file":
            if dst_scheme == "storage":
                if recursive:
                    return RecursiveLocalToPlatform(principal, progress)
                else:
                    return NonRecursiveLocalToPlatform(principal, progress)
            else:
                raise ValueError("storage:// and file:// schemes required")
        elif src_scheme == "storage":
            if dst_scheme == "file":
                if recursive:
                    return RecursivePlatformToLocal(principal, progress)
                else:
                    return NonRecursivePlatformToLocal(principal, progress)
            else:
                raise ValueError("storage:// and file:// schemes required")
        raise ValueError("storage:// and file:// schemes required")


class NonRecursivePlatformToLocal(CopyOperation):
    def transfer(self, file: FileStatus, i, o):  # pragma: no cover
        log.debug(f"Input: {i}")
        log.debug(f"Output: {o}")

        self.progress.start(file.path, file.size)
        copied = 0

        while True:
            buf = i.read(BUFFER_SIZE_MB * 1024 * 1024)

            if not buf:
                break

            copied = copied + len(buf)
            o.write(buf)
            self.progress.progress(file.path, copied)
        self.progress.complete(file.path)

    def copy_file(
        self, src: str, dst: str, file: FileStatus, storage
    ):  # pragma: no cover
        with storage() as s:
            with s.open(path=src) as stream:
                with open(dst, mode="wb") as f:
                    self.transfer(file, stream, f)
                    return dst

    def _copy(
        self, src: ParseResult, dst: ParseResult, storage: Callable
    ):  # pragma: no cover
        platform_file_name = self._render_platform_path_with_principal(src)

        # define local
        if os.path.exists(dst.path) and os.path.isdir(dst.path):
            #         get file name from src
            dst_path = Path(dst.path, platform_file_name.name)
        else:
            if dst.path.endswith(SYSTEM_PATH_DELIMITER):
                raise NotADirectoryError(
                    "Target should exist. "
                    "Please create directory, or point to existing file."
                )

            try_dir = dirname(dst.path)
            if try_dir != "" and not os.path.isdir(try_dir):
                raise FileNotFoundError(
                    "Target should exist. "
                    "Please create directory, or point to existing file."
                )
            dst_path = Path(dst.path)

        # check remote
        file_info = self._file_stat_on_platform(platform_file_name, storage)
        if not file_info or file_info.type != "FILE":
            raise ResourceNotFound(f"Source file {src.path} not found.")

        copy_file = self.copy_file(
            str(platform_file_name), str(dst_path), file_info, storage
        )
        return copy_file


class RecursivePlatformToLocal(NonRecursivePlatformToLocal):
    def _copy_obj(self, src: PosixPath, dst: Path, storage: Callable):
        files: List[FileStatus] = PlatformListDirOperation(self.principal).ls(
            path_str=f"storage:/{src}", storage=storage
        )

        for file in files:
            name = file.path
            target = Path(dst, name)
            if file.type == "DIRECTORY":
                os.mkdir(target)
                self._copy_obj(PosixPath(src, name), target, storage)
            else:
                platform_file_name = f"{src}{PLATFORM_DELIMITER}{name}"
                self.copy_file(platform_file_name, str(target), file, storage)

    def _is_local_dir(self, path: str) -> bool:
        return os.path.exists(path) and os.path.isdir(path)

    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        # Test if source is file or directory
        platform_file_name = self._render_platform_path_with_principal(src)
        file_status = self._file_stat_on_platform(platform_file_name, storage)
        if not file_status:
            raise FileNotFoundError("Source file not found.")

        if file_status.type == "FILE":
            copy_operation = NonRecursivePlatformToLocal(self.principal, self.progress)
            return copy_operation.copy(src, dst, storage)

        if file_status.type == "DIRECTORY":
            target_dir_name = PurePath(src.path).name
            target_dir = f"{dst.path}{os.sep}{target_dir_name}"
            if not self._is_local_dir(dst.path):
                parent_dir = os.path.dirname(dst.path)
                if not self._is_local_dir(parent_dir):
                    raise NotADirectoryError(
                        "Target should exist. Please create target directory "
                        "and try again."
                    )
                target_dir = f"{dst.path}"

            log.debug(target_dir)
            os.mkdir(target_dir)
            if not os.path.isdir(target_dir):
                raise NotADirectoryError(
                    "Target should be directory. Please correct your "
                    "command line arguments."
                )

            self._copy_obj(platform_file_name, Path(target_dir), storage)
            return dst.path


class NonRecursiveLocalToPlatform(CopyOperation):
    async def _copy_data_with_progress(self, src: str):  # pragma: no cover
        file_stat = os.stat(src)
        total_file_size = file_stat.st_size
        copied_file_size = 0
        self.progress.start(src, total_file_size)
        with open(src, mode="rb") as f:
            data_chunk = f.read(BUFFER_SIZE_B)
            while data_chunk:
                copied_file_size += len(data_chunk)
                yield data_chunk
                self.progress.progress(src, copied_file_size)
                data_chunk = f.read(BUFFER_SIZE_B)
            self.progress.complete(src)

    def copy_file(
        self, src_path: str, dest_path: str, storage: Callable
    ):  # pragma: no cover
        data = self._copy_data_with_progress(src_path)
        with storage() as s:
            s.create(path=dest_path, data=data)
            return dest_path

    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise FileNotFoundError("Source file not found.")

        if os.path.isdir(src.path):
            raise IsADirectoryError("Source should be file.")

        target_path: PosixPath = self._render_platform_path_with_principal(dst)
        target_dir_not_exists = "Target directory does not exist."
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
        return f"storage:/{copy_file}"


class RecursiveLocalToPlatform(NonRecursiveLocalToPlatform):
    def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise ValueError("Source should exist.")

        if not os.path.isdir(src.path):
            return NonRecursiveLocalToPlatform._copy(self, src, dst, storage)

        final_path = self._render_platform_path_with_principal(dst)
        src_dir_path = PurePath(src.path).name
        if src_dir_path != "":
            final_path = PosixPath(final_path, src_dir_path)

        for root, subdirs, files in os.walk(src.path):
            if root != src.path:
                suffix_path = os.path.relpath(root, src.path)
                pref_path = f"{final_path}{PLATFORM_DELIMITER}"
                pref_path = f"{pref_path}{suffix_path}{PLATFORM_DELIMITER}"
            else:
                suffix_path = ""
                pref_path = f"{final_path}{PLATFORM_DELIMITER}"
            for file in files:
                target_dest = f"{pref_path}{file}"
                src_file = os.path.join(root, file)
                self.copy_file(src_file, target_dest, storage)
            for subdir in subdirs:
                target_dest = f"{pref_path}{subdir}"
                PlatformMakeDirOperation(self.principal).mkdir(
                    f"storage:/{target_dest}", storage
                )
        return final_path


class DockerHandler(PlatformOperation):
    def __init__(self, principal: str, token: str) -> None:
        super().__init__(principal, token)
        self._client = docker.APIClient()

    def _is_docker_available(self) -> bool:
        try:
            self._client.ping()
            return True
        except APIError:
            return False

    def _auth(self) -> Dict[str, str]:
        return {"username": "token", "password": self._token}

    @classmethod
    def _split_tagged_image_name(cls, image_name: str):
        colon_count = image_name.count(":")
        if colon_count == 0:
            return image_name, ""
        if colon_count == 1:
            name, tag = image_name.split(":")
            if name:
                return name, tag
        raise ValueError(f"Invalid image name format: {image_name}")

    def push(self, registry: str, image_name: str) -> str:
        if self._is_docker_available():
            try:
                image, tag = self._split_tagged_image_name(image_name)

                repository_url = f"{registry}/{self._principal}/{image}:{tag}"
                if not self._client.tag(image_name, repository_url, tag, force=True):
                    raise ValueError("Error tagging image.")
                progress = "|\\-/"
                cnt = 0
                for line in self._client.push(
                    repository_url,
                    stream=True,
                    decode=True,
                    tag=tag,
                    auth_config=self._auth(),
                ):  # pragma no cover
                    cnt = (cnt + 1) % len(progress)
                    print(f"\r{progress[cnt]}", end="")
                return repository_url
            except docker.errors.APIError as e:
                raise ValueError(
                    f"Cannot push container image to registry. Error {e.explanation}"
                ) from e

    def pull(self, registry: str, image_name: str) -> str:
        if self._is_docker_available():
            try:
                image, tag = self._split_tagged_image_name(image_name)

                repository_url = image
                progress = "|\\-/"
                cnt = 0
                for line in self._client.pull(
                    repository_url,
                    tag=tag,
                    stream=True,
                    decode=True,
                    auth_config=self._auth(),
                ):  # pragma no cover
                    cnt = (cnt + 1) % len(progress)
                    print(f"\r{progress[cnt]}", end="")
                return repository_url
            except docker.errors.APIError as e:
                log.error(e)
                raise ValueError(
                    f"Cannot pull container image from registry. Error {e.explanation}"
                ) from e
