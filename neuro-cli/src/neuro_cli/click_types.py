import abc
import os
import re
from datetime import datetime, timedelta
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
from click.shell_completion import (
    BashComplete,
    CompletionItem,
    ZshComplete,
    add_completion_class,
)
from yarl import URL

from neuro_sdk import (
    Client,
    LocalImage,
    Preset,
    RemoteImage,
    ResourceNotFound,
    TagOption,
)

from .parse_utils import (
    JobTableFormat,
    parse_ps_columns,
    parse_top_columns,
    to_megabytes,
)
from .root import Root

# NOTE: these job name defaults are taken from `platform_api` file `validators.py`
JOB_NAME_MIN_LENGTH = 3
JOB_NAME_MAX_LENGTH = 40
JOB_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
JOB_NAME_REGEX = re.compile(JOB_NAME_PATTERN)
JOB_LIMIT_ENV = "NEURO_CLI_JOB_AUTOCOMPLETE_LIMIT"


# NOTE: these disk name validation are taken from `platform_disk_api` file `schema.py`
DISK_NAME_MIN_LENGTH = 3
DISK_NAME_MAX_LENGTH = 40
DISK_NAME_PATTERN = "^[a-z](?:-?[a-z0-9])*$"
DISK_NAME_REGEX = re.compile(JOB_NAME_PATTERN)


# NOTE: these bucket name validation are taken from
# `platform_buckets_api` file `schema.py`
BUCKET_NAME_MIN_LENGTH = 3
BUCKET_NAME_MAX_LENGTH = 40
BUCKET_NAME_PATTERN = "^[a-z](?:-?[a-z0-9_-])*$"
BUCKET_NAME_REGEX = re.compile(JOB_NAME_PATTERN)


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


class BucketNameType(click.ParamType):
    name = "bucket_name"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        if (
            len(value) < BUCKET_NAME_MIN_LENGTH
            or len(value) > BUCKET_NAME_MAX_LENGTH
            or BUCKET_NAME_REGEX.match(value) is None
        ):
            raise ValueError(
                f"Invalid bucket name '{value}'.\n"
                "The name can only contain lowercase letters, numbers and "
                "hyphens and underscores with the following rules: \n"
                "  - the first character must be a letter; \n"
                "  - each hyphen/underscore must be surrounded by non-hyphen "
                "characters; \n"
                f"  - total length must be between {BUCKET_NAME_MIN_LENGTH} and "
                f"{BUCKET_NAME_MAX_LENGTH} characters long."
            )
        return value


BUCKET_NAME = BucketNameType()


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
        return root.client.parse.str_to_uri(
            value,
            allowed_schemes=self._allowed_schemes,
            short=False,
        )

    def _make_item(
        self,
        parent: URL,
        name: str,
        is_dir: bool,
    ) -> CompletionItem:
        if is_dir:
            name += "/"
        return CompletionItem(
            name,
            type="uri",
            prefix=str(parent) + "/" if parent.path else str(parent),
        )

    async def _collect_names(
        self,
        uri: URL,
        root: Root,
        incomplete: str,
    ) -> AsyncIterator[CompletionItem]:
        if uri.scheme == "file":
            path = root.client.parse.uri_to_path(uri)
            if not path.is_dir():
                raise NotADirectoryError
            for item in path.iterdir():
                if str(uri / item.name).startswith(incomplete):
                    is_dir = item.is_dir()
                    if is_dir and not self._complete_dir:
                        continue
                    if not is_dir and not self._complete_file:
                        continue
                    yield self._make_item(
                        uri,
                        item.name,
                        is_dir,
                    )
        else:
            async with root.client.storage.list(uri) as it:
                async for fstat in it:
                    if str(uri / fstat.name).startswith(incomplete):
                        is_dir = fstat.is_dir()
                        if is_dir and not self._complete_dir:
                            continue
                        if not is_dir and not self._complete_file:
                            continue
                        yield self._make_item(
                            uri,
                            fstat.name,
                            is_dir,
                        )

    async def _find_matches(self, incomplete: str, root: Root) -> List[CompletionItem]:
        ret: List[CompletionItem] = []
        for scheme in self._allowed_schemes:
            scheme += ":"
            if incomplete.startswith(scheme):
                # found valid scheme, try to resolve path
                break
            if scheme.startswith(incomplete):
                ret.append(CompletionItem(scheme, type="uri", prefix=""))
        else:
            return ret

        # while incomplete.endswith("/"):
        #     incomplete = incomplete[:-1]

        uri = root.client.parse.str_to_uri(
            incomplete,
            allowed_schemes=self._allowed_schemes,
            short=True,
        )
        try:
            return [item async for item in self._collect_names(uri, root, incomplete)]
        except (ResourceNotFound, NotADirectoryError):
            try:
                return [
                    item
                    async for item in self._collect_names(uri.parent, root, incomplete)
                ]
            except (ResourceNotFound, NotADirectoryError):
                return []

    async def async_shell_complete(
        self, root: Root, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:
        async with await root.init_client():
            ret = await self._find_matches(incomplete, root)
            return ret


_SOURCE_ZSH = """\
#compdef %(prog_name)s

%(complete_func)s() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    local -a uris
    local prefix
    (( ! $+commands[%(prog_name)s] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) \
%(complete_var)s=zsh_complete %(prog_name)s)}")

    for type key descr pre in ${response}; do
        if [[ "$type" == "uri" ]]; then
            uris+=("$key")
            prefix="$pre"
        elif [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
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
        compadd -P "$prefix" -S '' -U -V unsorted -a uris
    fi
}

compdef %(complete_func)s %(prog_name)s;
"""


class NewZshComplete(ZshComplete):
    source_template = _SOURCE_ZSH

    def format_completion(self, item: CompletionItem) -> str:
        return (
            f"{item.type}\n{item.value}\n{item.help if item.help else '_'}\n"
            f"{item.prefix}"
        )


add_completion_class(NewZshComplete)


_SOURCE_BASH = """\
%(complete_func)s() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD \
%(complete_var)s=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value prefix <<< "$completion"

        if [[ $type == 'uri' ]]; then
            COMPREPLY+=("$prefix$value")
            compopt -o nospace
        elif [[ $type == 'dir' ]]; then
            COMREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

%(complete_func)s_setup() {
    complete -o nosort -F %(complete_func)s %(prog_name)s
}

%(complete_func)s_setup;
"""


def _merge_autocompletion_args(
    args: List[str], incomplete: str
) -> Tuple[List[str], str]:
    new_args: List[str] = []
    for arg in args:
        if arg == ":":
            if new_args:
                new_args[-1] += ":"
            else:
                new_args.append(":")
        else:
            if new_args and new_args[-1].endswith(":"):
                new_args[-1] += arg
            else:
                new_args.append(arg)

    if new_args:
        if new_args[-1].endswith(":"):
            incomplete = new_args[-1] + incomplete
            del new_args[-1]
        elif incomplete == ":":
            incomplete = new_args[-1] + ":"
            del new_args[-1]
    return new_args, incomplete


class NewBashComplete(BashComplete):
    source_template = _SOURCE_BASH

    def get_completion_args(self) -> Tuple[List[str], str]:
        args, incomplete = super().get_completion_args()
        args, incomplete = _merge_autocompletion_args(args, incomplete)
        return args, incomplete

    def format_completion(self, item: CompletionItem) -> str:
        # bash assumes ':' as a word separator along with ' '
        pre, sep, prefix = (item.prefix or "").rpartition(":")
        return f"{item.type},{item.value},{prefix}"


add_completion_class(NewBashComplete)


class BucketType(AsyncType[str]):
    name = "bucket"

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
            async with client.buckets.list(
                cluster_name=ctx.params.get("cluster")
            ) as it:
                async for bucket in it:
                    bucket_name = bucket.name or ""
                    for test in (
                        bucket.id,
                        bucket_name,
                    ):
                        if test.startswith(incomplete):
                            ret.append(CompletionItem(test, help=bucket_name))

            return ret


BUCKET = BucketType()


class BucketCredentialType(AsyncType[str]):
    name = "bucket_credential"

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
            async with client.buckets.persistent_credentials_list(
                cluster_name=ctx.params.get("cluster")
            ) as it:
                async for credential in it:
                    credential_name = credential.name or ""
                    for test in (
                        credential.id,
                        credential_name,
                    ):
                        if test.startswith(incomplete):
                            ret.append(CompletionItem(test, help=credential_name))

            return ret


BUCKET_CREDENTIAL = BucketCredentialType()
