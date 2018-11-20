import abc
import datetime
import logging
import os
import subprocess
from os.path import dirname
from pathlib import Path, PosixPath, PurePath, PurePosixPath
from time import sleep
from typing import Callable, Dict, List, Optional
from urllib.parse import ParseResult, urlparse

import dateutil.parser

from neuromation import Resources
from neuromation.cli.command_progress_report import ProgressBase
from neuromation.client import FileStatus, Image, ResourceNotFound
from neuromation.client.jobs import JobDescription, NetworkPortForwarding
from neuromation.client.requests import VolumeDescriptionPayload
from neuromation.http import BadRequestError


log = logging.getLogger(__name__)

BUFFER_SIZE_MB = 1

BUFFER_SIZE_B = BUFFER_SIZE_MB * 1024 * 1024

PLATFORM_DELIMITER = "/"

SYSTEM_PATH_DELIMITER = os.sep


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
    async def share(
        self, path_str: str, op_type: str, whom: str, resource_sharing: Callable
    ):
        what = urlparse(path_str, scheme="file")
        target_platform_path = self._render_platform_path_with_principal(what)
        async with resource_sharing() as rs:
            resource_uri = f"{what.scheme}:/{target_platform_path}"
            return await rs.share(resource_uri, op_type, whom)


class PlatformMakeDirOperation(PlatformStorageOperation):
    async def mkdir(self, path_str: str, storage: Callable):
        final_path = self.render_uri_path_with_principal(path_str)
        # TODO CHECK parent exists
        async with storage() as s:
            return await s.mkdirs(path=str(final_path))


class PlatformListDirOperation(PlatformStorageOperation):
    async def ls(self, path_str: str, storage: Callable) -> List[FileStatus]:
        final_path = self.render_uri_path_with_principal(path_str)
        async with storage() as s:
            return await s.ls(path=str(final_path))


class PlatformRemoveOperation(PlatformStorageOperation):
    async def remove(self, path_str: str, storage: Callable):
        path = urlparse(path_str, scheme="file")
        self._is_storage_path_url(path)
        final_path = self.render_uri_path_with_principal(path_str)

        root_data_path = PosixPath("/")

        # Minor protection against deleting everything from root
        # or user volume root, however force operation here should
        # allow user to delete everything
        if final_path == root_data_path or final_path.parent == root_data_path:
            raise ValueError("Invalid path value.")

        async with storage() as s:
            return await s.rm(path=str(final_path))


class PlatformRenameOperation(PlatformStorageOperation):
    async def mv(self, src_str: str, dst_str: str, storage: Callable):
        src_path_str = str(self.render_uri_path_with_principal(src_str))
        dst_path_str = str(self.render_uri_path_with_principal(dst_str))
        async with storage() as s:
            return await s.mv(src_path=src_path_str, dst_path=dst_path_str)


class CopyOperation(PlatformStorageOperation):
    def __init__(self, principal: str, progress: ProgressBase):
        super().__init__(principal)
        self.progress = progress

    async def _file_stat_on_platform(
        self, path: PosixPath, storage: Callable
    ) -> Optional[FileStatus]:
        try:
            async with storage() as s:
                file_status = await s.stats(path=str(path))
                return file_status
        except ResourceNotFound:
            return None

    @abc.abstractmethod
    async def _copy(
        self, src: ParseResult, dst: ParseResult, storage: Callable
    ):  # pragma: no cover
        pass

    async def copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        log.debug(f"Copy {src} to {dst}.")
        copy_result = await self._copy(src, dst, storage)
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
    async def transfer(self, file: FileStatus, i, o):  # pragma: no cover
        log.debug(f"Input: {i}")
        log.debug(f"Output: {o}")

        self.progress.start(file.path, file.size)
        copied = 0

        while True:
            buf = await i.read()

            if not buf:
                break

            copied = copied + len(buf)
            o.write(buf)
            self.progress.progress(file.path, copied)
        self.progress.complete(file.path)

    async def copy_file(
        self, src: str, dst: str, file: FileStatus, storage
    ):  # pragma: no cover
        async with storage() as s:
            async with s.open(path=src) as stream:
                with open(dst, mode="wb") as f:
                    await self.transfer(file, stream, f)
                    return dst

    async def _copy(
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
        file_info = await self._file_stat_on_platform(platform_file_name, storage)
        if not file_info or file_info.type != "FILE":
            raise ResourceNotFound(f"Source file {src.path} not found.")

        copy_file = await self.copy_file(
            str(platform_file_name), str(dst_path), file_info, storage
        )
        return copy_file


class RecursivePlatformToLocal(NonRecursivePlatformToLocal):
    async def _copy_obj(self, src: PosixPath, dst: Path, storage: Callable):
        files: List[FileStatus] = await PlatformListDirOperation(self.principal).ls(
            path_str=f"storage:/{src}", storage=storage
        )

        for file in files:
            name = file.path
            target = Path(dst, name)
            if file.type == "DIRECTORY":
                os.mkdir(target)
                await self._copy_obj(PosixPath(src, name), target, storage)
            else:
                platform_file_name = f"{src}{PLATFORM_DELIMITER}{name}"
                await self.copy_file(platform_file_name, str(target), file, storage)

    async def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(dst.path):
            raise FileNotFoundError(
                "Target should exist. " "Please create target directory and try again."
            )

        if not os.path.isdir(dst.path):
            raise NotADirectoryError(
                "Target should be directory. "
                "Please correct your command line arguments."
            )

        # Test that source directory exists.
        platform_file_name = self._render_platform_path_with_principal(src)
        # TODO here we should have work around when someone
        # tries to copy full directory of a person
        if str(platform_file_name) != "/":
            files = await self._file_stat_on_platform(platform_file_name, storage)
            if not files:
                raise ResourceNotFound("Source directory not found.")
            if files.type == "FILE":
                copy_operation = NonRecursivePlatformToLocal(
                    self.principal, self.progress
                )
                return await copy_operation.copy(src, dst, storage)

        await self._copy_obj(platform_file_name, Path(dst.path), storage)

        return dst.path


class NonRecursiveLocalToPlatform(CopyOperation):
    async def _is_dir_on_platform(self, path: PosixPath, storage: Callable) -> bool:
        """Tests whether specified path is directory on a platform or not."""
        try:
            async with storage() as s:
                file_status = await s.stats(path=str(path))
                return file_status.type == "DIRECTORY"
        except ResourceNotFound:
            return False

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

    async def copy_file(
        self, src_path: str, dest_path: str, storage: Callable
    ):  # pragma: no cover
        data = self._copy_data_with_progress(src_path)
        async with storage() as s:
            await s.create(path=dest_path, data=data)
            return dest_path

    async def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise FileNotFoundError("Source file not found.")

        if os.path.isdir(src.path):
            raise IsADirectoryError("Source should be file.")

        target_path: PosixPath = self._render_platform_path_with_principal(dst)
        target_dir_not_exists = "Target directory does not exist."
        if len(dst.path) and dst.path[-1] == PLATFORM_DELIMITER:
            if not await self._is_dir_on_platform(target_path, storage):
                raise NotADirectoryError(target_dir_not_exists)
            target_path = PosixPath(target_path, Path(src.path).name)
        else:
            if not await self._is_dir_on_platform(target_path, storage):
                if not await self._is_dir_on_platform(target_path.parent, storage):
                    raise NotADirectoryError(target_dir_not_exists)
            else:
                target_path = PosixPath(target_path, Path(src.path).name)

        copy_file = await self.copy_file(src.path, str(target_path), storage)
        return f"storage:/{copy_file}"


class RecursiveLocalToPlatform(NonRecursiveLocalToPlatform):
    async def _copy(self, src: ParseResult, dst: ParseResult, storage: Callable):
        if not os.path.exists(src.path):
            raise ValueError("Source should exist.")

        if not os.path.isdir(src.path):
            return await NonRecursiveLocalToPlatform._copy(self, src, dst, storage)

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
                await self.copy_file(src_file, target_dest, storage)
            for subdir in subdirs:
                target_dest = f"{pref_path}{subdir}"
                await PlatformMakeDirOperation(self.principal).mkdir(
                    f"storage:/{target_dest}", storage
                )
        return final_path


class JobHandlerOperations(PlatformStorageOperation):
    async def wait_job_transfer_from(
        self, id: str, from_state: str, jobs: Callable, sleep_interval_s: int = 1
    ) -> JobDescription:
        still_state = True
        job_status = None
        while still_state:
            job_status = await self.status(id, jobs)
            still_state = job_status.status == from_state
            if still_state:
                sleep(sleep_interval_s)
        return job_status

    def _validate_args_for_ssh_session(
        self, container_user: str, container_key: str, jump_host_key: str
    ):
        # Temporal solution - pending custom Jump Server with JWT support
        if not container_user:
            raise ValueError("Specify container user name")
        if not container_key:
            raise ValueError("Specify container RSA key path.")
        if not jump_host_key:
            raise ValueError(
                "Configure Github RSA key path." "See for more info `neuro config`."
            )

    def _validate_job_status_for_ssh_session(self, job_status: JobDescription):
        if job_status.status == "running":
            if job_status.ssh:
                pass
            else:
                raise ValueError("Job should be started with SSH support.")
        else:
            raise ValueError(f"Job is not running. Job status is {job_status.status}")

    async def status(self, id: str, jobs: Callable) -> JobDescription:
        async with jobs() as j:
            return await j.status(id)

    @classmethod
    def _truncate_string(cls, input: str, max_length: int) -> str:
        if len(input) <= max_length:
            return input
        len_tail, placeholder = 3, "..."
        if max_length < len_tail or max_length < len(placeholder):
            return placeholder
        tail = input[-len_tail:] if max_length > len(placeholder) + len_tail else ""
        index_stop = max_length - len(placeholder) - len(tail)
        return input[:index_stop] + placeholder + tail

    @classmethod
    def _format_full_job_line(cls, item: JobDescription) -> str:
        def wrap(text: str) -> str:
            return f"'{text}'" if text else ""

        tab = "\t"
        image = item.image or ""
        description = wrap(cls._truncate_string(item.description or "", 50))
        command = wrap(cls._truncate_string(item.command or "", 50))
        return tab.join(
            [
                item.id,
                f"{item.status:<10}",
                f"{image:<15}",
                f"{description:<50}",
                f"{command:<50}",
            ]
        )

    @classmethod
    def _sort_job_list(cls, job_list: List[JobDescription]) -> List[JobDescription]:
        def job_sorting_key_by_creation_time(job: JobDescription) -> datetime:
            created_str = job.history.created_at
            return dateutil.parser.isoparse(created_str)

        return sorted(job_list, key=job_sorting_key_by_creation_time)

    async def list_jobs(
        self,
        jobs: Callable,
        status: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        def apply_filter(item: JobDescription) -> bool:
            filter_status = not status or item.status == status
            filter_description = not description or item.description == description
            return filter_status and filter_description

        async with jobs() as j:
            job_list = await j.list()
            return "\n".join(
                [
                    self._format_full_job_line(item)
                    for item in self._sort_job_list(job_list)
                    if apply_filter(item)
                ]
            )

    def _network_parse(self, http, ssh) -> Optional[NetworkPortForwarding]:
        net = None
        ports: Dict[str, int] = {}
        if http:
            ports["http"] = int(http)
        if ssh:
            ports["ssh"] = int(ssh)
        if ports:
            net = NetworkPortForwarding(ports)
        return net

    def _parse_volume_str(self, volume: str) -> VolumeDescriptionPayload:
        volume_desc_parts = volume.split(":")
        if len(volume_desc_parts) != 3 and len(volume_desc_parts) != 4:
            raise ValueError(f"Invalid volume specification '{volume}'")

        storage_path = ":".join(volume_desc_parts[:-1])
        container_path = volume_desc_parts[2]
        read_only = False
        if len(volume_desc_parts) == 4:
            if not volume_desc_parts[-1] in ["ro", "rw"]:
                raise ValueError(f"Wrong ReadWrite/ReadOnly mode spec for '{volume}'")
            read_only = volume_desc_parts[-1] == "ro"
            storage_path = ":".join(volume_desc_parts[:-2])

        self._is_storage_path_url(urlparse(storage_path, scheme="file"))
        storage_path_with_principal = (
            f"storage:/{str(self.render_uri_path_with_principal(storage_path))}"
        )

        return VolumeDescriptionPayload(
            storage_path_with_principal, container_path, read_only
        )

    def _parse_volumes(self, volumes) -> Optional[List[VolumeDescriptionPayload]]:
        if volumes:
            try:
                return [self._parse_volume_str(volume) for volume in volumes]
            except ValueError as e:
                raise ValueError from e
        return None

    async def submit(
        self,
        image,
        gpu: str,
        gpu_model: str,
        cpu: str,
        memory: str,
        extshm: str,
        cmd,
        http,
        ssh,
        volumes,
        jobs: Callable,
        description: str,
    ) -> JobDescription:

        cmd = " ".join(cmd) if cmd is not None else None
        log.debug(f'cmd="{cmd}"')

        async with jobs() as j:
            image = Image(image=image, command=cmd)
            network = self._network_parse(http, ssh)
            resources = Resources.create(cpu, gpu, gpu_model, memory, extshm)
            volumes = self._parse_volumes(volumes)
            return await j.submit(
                image=image,
                resources=resources,
                network=network,
                volumes=volumes,
                description=description,
            )

    def start_ssh(
        self,
        job_id: str,
        jump_host: str,
        jump_user: str,
        jump_key: str,
        container_user: str,
        container_key: str,
    ):
        nc_command = f"nc {job_id} 22"
        proxy_command = (
            f"ProxyCommand=ssh -i {jump_key} {jump_user}@{jump_host} {nc_command}"
        )
        try:
            subprocess.run(
                args=[
                    "ssh",
                    "-o",
                    proxy_command,
                    "-i",
                    container_key,
                    f"{container_user}@{job_id}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # TODO (R Zubairov) check what ssh returns
            # on disconnect due to network issues.
            pass
        return None

    def _start_ssh_tunnel(
        self,
        job_status: JobDescription,
        jump_host: str,
        jump_user: str,
        jump_key: str,
        local_port: int,
    ) -> None:
        self._validate_job_status_for_ssh_session(job_status)
        try:
            subprocess.run(
                args=[
                    "ssh",
                    "-i",
                    jump_key,
                    f"{jump_user}@{jump_host}",
                    "-f",
                    "-N",
                    "-L",
                    f"{local_port}:{job_status.id}:22",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # TODO (R Zubairov) check what ssh returns
            # on disconnect due to network issues.
            pass

    def _connect_ssh(
        self,
        job_status: JobDescription,
        jump_host_key: str,
        container_user: str,
        container_key: str,
    ):
        self._validate_job_status_for_ssh_session(job_status)
        # We shall make an attempt to connect only in case it has SSH
        ssh_hostname = job_status.jump_host()
        self.start_ssh(
            job_status.id,
            ssh_hostname,
            self.principal,
            jump_host_key,
            container_user,
            container_key,
        )
        return None

    async def connect_ssh(
        self,
        job_id: str,
        jump_host_key: str,
        container_user: str,
        container_key: str,
        jobs: Callable,
    ) -> None:
        self._validate_args_for_ssh_session(
            container_user, container_key, jump_host_key
        )
        # Check if job is running
        try:
            job_status = await self.status(job_id, jobs)
            self._connect_ssh(job_status, jump_host_key, container_user, container_key)
        except BadRequestError as e:
            raise ValueError(f"Job not found. Job Id = {job_id}") from e

    async def python_remote_debug(
        self, job_id: str, jump_host_key: str, local_port: int, jobs: Callable
    ) -> None:
        if not jump_host_key:
            raise ValueError(
                "Configure Github RSA key path." "See for more info `neuro config`."
            )
        try:
            job_status = await self.status(job_id, jobs)
            ssh_hostname = job_status.jump_host()
            self._start_ssh_tunnel(
                job_status, ssh_hostname, self.principal, jump_host_key, local_port
            )
        except BadRequestError as e:
            raise ValueError(f"Job not found. Job Id = {job_id}") from e


class ModelHandlerOperations(JobHandlerOperations):
    async def train(
        self,
        image,
        dataset,
        results,
        gpu,
        gpu_model,
        cpu,
        memory,
        extshm,
        cmd,
        model,
        http,
        ssh,
        description: str,
    ):
        try:
            dataset_platform_path = self.render_uri_path_with_principal(dataset)
        except ValueError as e:
            raise ValueError(
                f"Dataset path should be on platform. " f"Current value {dataset}"
            )

        try:
            resultset_platform_path = self.render_uri_path_with_principal(results)
        except ValueError as e:
            raise ValueError(
                f"Results path should be on platform. " f"Current value {results}"
            )

        net = self._network_parse(http, ssh)

        cmd = " ".join(cmd) if cmd is not None else None
        log.debug(f'cmd="{cmd}"')

        async with model() as m:
            job = await m.train(
                image=Image(image=image, command=cmd),
                network=net,
                resources=Resources.create(cpu, gpu, gpu_model, memory, extshm),
                dataset=f"storage:/{dataset_platform_path}",
                results=f"storage:/{resultset_platform_path}",
                description=description,
            )

        return job
