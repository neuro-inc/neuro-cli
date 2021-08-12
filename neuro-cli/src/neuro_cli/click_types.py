import abc
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import (
    AsyncIterator,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import click
from click import BadParameter
from click.shell_completion import CompletionItem, ZshComplete, add_completion_class
from yarl import URL

from neuro_sdk import (
    Client,
    LocalImage,
    Preset,
    RemoteImage,
    ResourceNotFound,
    TagOption,
)
from neuro_sdk.url_utils import _extract_path, uri_from_cli

from .parse_utils import (
    JobTableFormat,
    parse_ps_columns,
    parse_top_columns,
    to_megabytes,
)
from .root import Root
from .utils import _calc_relative_uri

# NOTE: these job name defaults are taken from `platform_api` file `validators.py`
JOB_NAME_MIN_LENGTH = 3
JOB_NAME_MAX_LENGTH = 40
JOB_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
JOB_NAME_REGEX = re.compile(JOB_NAME_PATTERN)
JOB_LIMIT_ENV = "NEURO_CLI_JOB_AUTOCOMPLETE_LIMIT"


# NOTE: these disk name valdation are taken from `platform_disk_api` file `schema.py`
DISK_NAME_MIN_LENGTH = 3
DISK_NAME_MAX_LENGTH = 40
DISK_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
DISK_NAME_REGEX = re.compile(JOB_NAME_PATTERN)

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

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        root = cast(Root, ctx.obj)
        return root.run(self.async_shell_complete(root, ctx, param, incomplete))

    @abc.abstractmethod
    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
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


class RemoteTaglessImageType(click.ParamType):
    name = "image"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        client = root.run(root.init_client())
        return client.parse.remote_image(value, tag_option=TagOption.DENY)


class RemoteImageType(click.ParamType):
    name = "image"

    def __init__(self, tag_option: TagOption = TagOption.DEFAULT) -> None:
        self.tag_option = tag_option

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> RemoteImage:
        assert ctx is not None
        root = cast(Root, ctx.obj)
        cluster_name = ctx.params.get("cluster")
        client = root.run(root.init_client())
        return client.parse.remote_image(
            value, tag_option=self.tag_option, cluster_name=cluster_name
        )


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
        if isinstance(value, int):
            return int(value / (1024 ** 2))
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


class DiskNameType(click.ParamType):
    name = "disk_name"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        if (
            len(value) < DISK_NAME_MIN_LENGTH
            or len(value) > DISK_NAME_MAX_LENGTH
            or DISK_NAME_REGEX.match(value) is None
        ):
            raise ValueError(
                f"Invalid disk name '{value}'.\n"
                "The name can only contain lowercase letters, numbers and hyphens "
                "with the following rules: \n"
                "  - the first character must be a letter; \n"
                "  - each hyphen must be surrounded by non-hyphen characters; \n"
                f"  - total length must be between {DISK_NAME_MIN_LENGTH} and "
                f"{DISK_NAME_MAX_LENGTH} characters long."
            )
        return value


DISK_NAME = DiskNameType()


class JobColumnsType(click.ParamType):
    name = "columns"

    def convert(
        self,
        value: Union[str, JobTableFormat],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> JobTableFormat:
        if isinstance(value, list):
            return value
        return parse_ps_columns(value)


JOB_COLUMNS = JobColumnsType()


class TopColumnsType(click.ParamType):
    name = "columns"

    def convert(
        self,
        value: Union[str, JobTableFormat],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> JobTableFormat:
        if isinstance(value, list):
            return value
        return parse_top_columns(value)


TOP_COLUMNS = TopColumnsType()


class PresetType(AsyncType[str]):
    name = "preset"

    def _get_presets(
        self, ctx: Optional[click.Context], client: Client
    ) -> Mapping[str, Preset]:
        cluster_name = client.cluster_name
        if ctx:
            cluster_name = ctx.params.get("cluster", client.cluster_name)
        if cluster_name not in client.config.clusters:
            return {}
        return client.config.clusters[cluster_name].presets

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        client = await root.init_client()
        if value not in self._get_presets(ctx, client):
            cluster_name = client.cluster_name
            if ctx:
                cluster_name = ctx.params.get("cluster", client.cluster_name)
            if cluster_name != client.cluster_name:
                error_message = (
                    f"Preset {value} is not valid for cluster {cluster_name}."
                )
            else:
                error_message = f"Preset {value} is not valid, "
                "run 'neuro config show' to get a list of available presets"
            raise click.BadParameter(
                error_message,
                ctx,
                param,
            )
        return value

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        # async context manager is used to prevent a message about
        # unclosed session
        async with await root.init_client() as client:
            presets = list(self._get_presets(ctx, client))
            return [CompletionItem(p) for p in presets if p.startswith(incomplete)]


PRESET = PresetType()


class ClusterType(AsyncType[str]):
    name = "cluster"

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        client = await root.init_client()
        if value not in client.config.clusters:
            raise click.BadParameter(
                f"Cluster {value} is not valid, "
                "run 'neuro config get-clusters' to get a list of available clusters",
                ctx,
                param,
            )
        return value

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        # async context manager is used to prevent a message about
        # unclosed session
        async with await root.init_client() as client:
            clusters = list(client.config.clusters)
            return [CompletionItem(c) for c in clusters if c.startswith(incomplete)]


CLUSTER = ClusterType()


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

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        async with await root.init_client() as client:
            ret: List[CompletionItem] = []
            now = datetime.now()
            limit = int(os.environ.get(JOB_LIMIT_ENV, 100))
            async with client.jobs.list(
                since=now - timedelta(days=7), reverse=True, limit=limit
            ) as it:
                async for job in it:
                    job_name = job.name or ""
                    for test in (
                        job.id,
                        job_name,
                        f"job:{job.id}",
                        f"job:/{job.owner}/{job.id}",
                        f"job://{job.cluster_name}/{job.owner}/{job.id}",
                    ):
                        if test.startswith(incomplete):
                            ret.append(CompletionItem(test, help=job_name))

            return ret


JOB = JobType()


class DiskType(AsyncType[str]):
    name = "disk"

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        return value

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        async with await root.init_client() as client:
            ret: List[CompletionItem] = []
            async with client.disks.list(cluster_name=ctx.params.get("cluster")) as it:
                async for disk in it:
                    disk_name = disk.name or ""
                    for test in (
                        disk.id,
                        disk_name,
                    ):
                        if test.startswith(incomplete):
                            ret.append(CompletionItem(test, help=disk_name))

            return ret


DISK = DiskType()


class ServiceAccountType(AsyncType[str]):
    name = "disk"

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> str:
        return value

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        async with await root.init_client() as client:
            ret: List[CompletionItem] = []
            async with client.service_accounts.list() as it:
                async for account in it:
                    account_name = account.name or ""
                    for test in (
                        account.id,
                        account_name,
                    ):
                        if test.startswith(incomplete):
                            ret.append(CompletionItem(test, help=account_name))

            return ret


SERVICE_ACCOUNT = ServiceAccountType()


class StoragePathType(AsyncType[URL]):
    name = "storage"

    def __init__(
        self,
        *,
        allowed_schemes: Iterable[str] = ("file", "storage"),
        complete_dir: bool = True,
        complete_file: bool = True,
    ) -> None:
        self._allowed_schemes = list(allowed_schemes)
        self._complete_dir = complete_dir
        self._complete_file = complete_file

    async def async_convert(
        self,
        root: Root,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> URL:
        await root.init_client()
        return self._parse_uri(value, root)

    def _parse_uri(self, value: str, root: Root) -> URL:
        return uri_from_cli(
            value,
            root.client.username,
            root.client.cluster_name,
            allowed_schemes=self._allowed_schemes,
        )

    def _make_item(
        self,
        parent: URL,
        name: str,
        is_dir: bool,
        prefix: str,
    ) -> CompletionItem:
        uri = _calc_relative_uri(parent, name, prefix)
        if is_dir:
            return CompletionItem(
                uri + "/",
                uri="1",
                display_name=name + "/",
            )
        else:
            return CompletionItem(
                uri,
                uri="1",
                display_name=name,
            )

    async def _collect_names(
        self,
        uri: URL,
        root: Root,
        incomplete: str,
    ) -> AsyncIterator[CompletionItem]:
        if uri.scheme == "file":
            path = _extract_path(uri)
            if not path.is_dir():
                raise NotADirectoryError
            cwd = Path.cwd().as_uri()
            for item in path.iterdir():
                if str(item.name).startswith(incomplete):
                    is_dir = item.is_dir()
                    if is_dir and not self._complete_dir:
                        continue
                    if not is_dir and not self._complete_file:
                        continue
                    yield self._make_item(
                        uri,
                        item.name,
                        is_dir,
                        str(cwd),
                    )
        else:
            home = self._parse_uri("storage:", root)
            async with root.client.storage.ls(uri) as it:
                async for fstat in it:
                    if str(fstat.name).startswith(incomplete):
                        is_dir = fstat.is_dir()
                        if is_dir and not self._complete_dir:
                            continue
                        if not is_dir and not self._complete_file:
                            continue
                        yield self._make_item(
                            uri,
                            fstat.name,
                            is_dir,
                            str(home),
                        )

    async def _find_matches(self, incomplete: str, root: Root) -> List[CompletionItem]:
        ret: List[CompletionItem] = []
        for scheme in self._allowed_schemes:
            scheme += ":"
            if incomplete.startswith(scheme):
                # found valid scheme, try to resolve path
                break
            if scheme.startswith(incomplete):
                ret.append(CompletionItem(scheme, uri="1", display_name=scheme))
        else:
            return ret

        uri = self._parse_uri(incomplete, root)
        try:
            return [item async for item in self._collect_names(uri, root, "")]
        except (ResourceNotFound, NotADirectoryError):
            try:
                return [
                    item
                    async for item in self._collect_names(uri.parent, root, uri.name)
                ]
            except (ResourceNotFound, NotADirectoryError):
                return []

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        async with await root.init_client():
            return await self._find_matches(incomplete, root)


_SOURCE_ZSH = """\
#compdef %(prog_name)s

%(complete_func)s() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    local -a uris
    local -a display_names
    (( ! $+commands[%(prog_name)s] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) \
%(complete_var)s=zsh_complete %(prog_name)s)}")

    for type key descr uri display_name in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$uri" == "1" ]]; then
                uris+=("$key")
                display_names+=("$display_name")
            else
                if [[ "$descr" == "_" ]]; then
                    completions+=("$key")
                else
                    completions_with_descriptions+=("$key":"$descr")
                fi
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi

    if [ -n "$uris" ]; then
        compset -S '[^:/]*' && compstate[to_end]=''
        compadd -Q -S '' -d display_names -U -V unsorted -a uris
    fi
}


compdef %(complete_func)s %(prog_name)s;
"""


class NewZshComplete(ZshComplete):
    source_template = _SOURCE_ZSH

    def format_completion(self, item: CompletionItem) -> str:
        return (
            f"{item.type}\n{item.value}\n{item.help if item.help else '_'}\n"
            f"{item.uri}\n{item.display_name}"
        )


add_completion_class(NewZshComplete)
