import abc
import re
from datetime import datetime, timedelta
from typing import Generic, List, Optional, Sequence, Tuple, TypeVar, Union, cast

import click
from click import BadParameter

from neuromation.api import LocalImage, RemoteImage, TagOption

from .parse_utils import JobColumnInfo, parse_columns, to_megabytes
from .root import Root


# NOTE: these job name defaults are taken from `platform_api` file `validators.py`
JOB_NAME_MIN_LENGTH = 3
JOB_NAME_MAX_LENGTH = 40
JOB_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
JOB_NAME_REGEX = re.compile(JOB_NAME_PATTERN)


_T = TypeVar("_T")


class AsyncType(click.ParamType, Generic[_T], abc.ABC):
    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> _T:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        return root.run(self.async_convert(root, value, param, ctx))

    @abc.abstractmethod
    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> _T:
        pass

    def complete(
        self, ctx: click.Context, args: Sequence[str], incomplete: str
    ) -> List[Tuple[str, Optional[str]]]:
        root = cast(Root, ctx.obj)
        return root.run(self.async_complete(root, ctx, args, incomplete))

    @abc.abstractmethod
    async def async_complete(
        self, root: Root, ctx: click.Context, args: Sequence[str], incomplete: str
    ) -> List[Tuple[str, Optional[str]]]:
        pass


class LocalImageType(click.ParamType):
    name = "local_image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> LocalImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        client = root.run(root.init_client())
        return client.parse.local_image(value)


class ImageType(click.ParamType):
    name = "image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        client = root.run(root.init_client())
        return client.parse.remote_image(value)


class RemoteTaglessImageType(click.ParamType):
    name = "image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        client = root.run(root.init_client())
        return client.parse.remote_image(value, tag_option=TagOption.DENY)


class LocalRemotePortParamType(click.ParamType):
    name = "local-remote-port-pair"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Tuple[int, int]:
        try:
            local_str, remote_str = value.split(":")
            local, remote = int(local_str), int(remote_str)
            if not (0 < local <= 65535 and 0 < remote <= 65535):
                raise ValueError("Port should be in range 1 to 65535")
            return local, remote
        except ValueError as e:
            raise BadParameter(f"{value} is not a valid port combination: {e}")


LOCAL_REMOTE_PORT = LocalRemotePortParamType()


class MegabyteType(click.ParamType):
    name = "megabyte"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> int:
        return to_megabytes(value)


MEGABYTE = MegabyteType()


class JobNameType(click.ParamType):
    name = "job_name"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        if (
            len(value) < JOB_NAME_MIN_LENGTH
            or len(value) > JOB_NAME_MAX_LENGTH
            or JOB_NAME_REGEX.match(value) is None
        ):
            raise ValueError(
                f"Invalid job name '{value}'.\n"
                "The name can only contain lowercase letters, numbers and hyphens "
                "with the following rules: \n"
                "  - the first character must be a letter; \n"
                "  - each hyphen must be surrounded by non-hyphen characters; \n"
                f"  - total length must be between {JOB_NAME_MIN_LENGTH} and "
                f"{JOB_NAME_MAX_LENGTH} characters long."
            )
        return value


JOB_NAME = JobNameType()


class JobColumnsType(click.ParamType):
    name = "columns"

    def convert(
        self,
        value: Union[str, List[JobColumnInfo]],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> List[JobColumnInfo]:
        if isinstance(value, list):
            return value
        return parse_columns(value)


JOB_COLUMNS = JobColumnsType()


class PresetType(AsyncType[str]):
    name = "preset"

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        client = await root.init_client()
        if value not in client.presets:
            raise click.BadParameter(
                f"Preset {value} is not valid, "
                "run 'neuro config show' to get a list of available presets",
                ctx,
                param,
            )
        return value

    async def async_complete(
        self, root: Root, ctx: click.Context, args: Sequence[str], incomplete: str
    ) -> List[Tuple[str, Optional[str]]]:
        # async context manager is used to prevent a message about
        # unclosed session
        async with await root.init_client() as client:
            presets = list(client.config.presets)
            return [(p, None) for p in presets if p.startswith(incomplete)]


PRESET = PresetType()


class JobType(AsyncType[str]):
    name = "job"

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        return value

    async def async_complete(
        self, root: Root, ctx: click.Context, args: Sequence[str], incomplete: str
    ) -> List[Tuple[str, Optional[str]]]:
        async with await root.init_client() as client:
            ret: List[Tuple[str, Optional[str]]] = []
            now = datetime.now()
            async for job in client.jobs.list(
                since=now - timedelta(days=7), reverse=True, limit=100
            ):
                job_name = job.name or ""
                for test in (
                    job.id,
                    job_name,
                    f"job:{job.id}",
                    f"job:/{job.owner}/{job.id}",
                    f"job://{job.cluster_name}/{job.owner}/{job.id}",
                ):
                    if test.startswith(incomplete):
                        ret.append((test, job_name))

            return ret


JOB = JobType()
