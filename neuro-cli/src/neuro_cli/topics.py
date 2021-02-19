from typing import Any, Callable, Iterable, Optional, Type, cast

import click
from click.utils import make_default_short_help
from rich.markdown import Markdown

from .root import Root


class Command(click.Command):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if self.help is None:
            return
        formatter.write_paragraph()
        root = cast(Root, ctx.obj)
        with root.pager():
            root.print(Markdown(self.help, inline_code_lexer="bash"))

    def get_short_help_str(self, limit: int = 45) -> str:
        if self.help is None:
            return ""
        head, *tail = self.help.split("\n", 1)
        return make_default_short_help(head.strip(" *_.#"))


def command(
    name: Optional[str] = None, cls: Type[Command] = Command, **kwargs: Any
) -> Command:
    return click.command(name=name, cls=cls, **kwargs)  # type: ignore


class Group(click.Group):
    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Command]:
        def decorator(f: Callable[..., Any]) -> Command:
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], "Group"]:
        def decorator(f: Callable[..., Any]) -> Group:
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return sorted(self.commands)


def group(name: Optional[str] = None, **kwargs: Any) -> Group:
    kwargs.setdefault("cls", Group)
    return click.group(name=name, **kwargs)  # type: ignore


@group()
def topics() -> None:
    """Help topics."""


@topics.command()
async def ps_format() -> None:
    """\
    Format for columns specification
    ================================

    The format is a sequence of column specifications separated
    by commas or spaces: `{id}, {status}, {when}`.

    A column spec has a mandatory column id plus optional properties
    for indication of alignment, minimum and maximum column width,
    and optional column title: `{id;align=center;min=10;max=30;width=20;TITLE}`

    Here **id** is the column id, **align**, **min**, **max**, **width**
    are properties and **TITLE** is the column title.

    An alternative form is specifying the column id only without
    additional properties, in this case curly brackets can be omitted:
    `id, status, when` or `id status when` are valid formats.


    Available properties:

    * **align**: Column aligning, accepted values: left, right, center.
    * **min**: Minimal column width.
    * **max**: Maximal column width.
    * **width**: Default column width.

    All properties can be skipped, the default value for specified column ID
    is used in this case.

    The system recognizes the following columns:

    * **id** (ID): job id.
    * **name** (NAME): job name.
    * **tags** (TAGS): job tags.
    * **status** (STATUS): job status.
    * **when** (WHEN): time of the last update of job information.
    * **created** (CREATED): time of job creation.
    * **started** (STARTED): time of job statrting.
    * **finished** (FINISHED): time of job finishing.
    * **image** (IMAGE): job image.
    * **owner** (OWNER): job owner.
    * **cluster_name** (CLUSTER): job cluster name.
    * **description** (DESCRIPTION): job description.
    * **command** (COMMAND): job command to execute.
    * **life_span** (LIFE-SPAN): job life-span.
    * **workdir** (WORKDIR): default working directory inside a job.
    * **preset** (PRESET): resource configuration used for a job.

    Columns recognizes only in the `neuro top` command:

    * **cpu** (CPU): number of used CPUs.
    * **memory** (MEMORY (MB)): amount of used memory, in MB.
    * **gpu** (GPU (%)): used GPUs, in percents.
    * **gpu_memory** (GPU_MEMORY (MB)): amount of used GPU memory, in MB.

    By default all columns are left aligned and have no minimal and default widths.

    The column id is case insensitive, it can be shrinked to any unambiguous subset
    of the full name.  For example `{CLUSTER:max=20}` is a good column spec but
    `{C:max=20}` is not; it can be expanded into both `cluster_name` and `command`
    column ids.

    """


@topics.command()
async def top_format() -> None:
    pass


top_format.help = ps_format.help


@topics.command()
async def user_config() -> None:
    """\
    User configuration files
    ========================

    The Neuro client supports user configuration files to provide default values
    for particular command options, user defined command aliases etc.

    There are two configuration files: **global** and **local**, both are optional
    and can be absent.

    The global file is located in the standard neuro config path.  "neuro" CLI uses
    `~/.neuro` folder by default, the path for global config file is
    `~/.neuro/user.toml`.

    The local config file is named .neuro.toml, the CLI search for this file
    starting from the current folder up to the root directory.

    Found local and global configurations are merged.
    If a parameter is present are both global and local versions the local parameter
    take a precedence.

    Configuration files have a TOML format (a stricter version of well-known INI
    format). See `https://en.wikipedia.org/wiki/TOML` and
    `https://github.com/toml-lang/toml#toml` for the format specification details.

    Supported configuration sections and parameters:

    `[alias]` section
    -----------------

    A section for describing user-provided aliases.

    See `neuro help aliases` for details about avaiable section contents.

    `[job]` section
    ---------------

    A section for `neuro job` command group settings.

    **`cluster-name`**

    The name of active cluster which overrides global cluster name set by
    `neuro config switch-cluster`.  Can only be specified in **local**
    configuration file.

    **`ps-format`**

    Default value for `neuro ps --format=XXX` option.

    See `neuro help ps-format` for information about the value specification.

    **`top-format`**

    Default value for `neuro top --format=XXX` option.

    See `neuro help top-format` for information about the value specification.

    **`life-span`**

    Default job run-time limit for `neuro run --life-span=XXX` option.

    The value is a string in format `1d2h3m4s` (this example will set the limit to
    1 day, 2 hours, 3 minutes and 4 seconds). Some values can be missing, for example:
    `1d6h`, `30m`. No spaces are allowed between values.

    `[storage]` section
    -------------------

    A section for `neuro storage` command group settings.

    **`cp-exclude`**

    Default value for `neuro cp --exclude=XXX` and `neuro cp --include=YYY` options.

    The value is a list of shell wildcard patterns, a file or folder that matches a
    pattern is excluded from processing.

    The pattern can contain `*` and `?`, e.g. `["*.jpg"]` is for exclusion of all
    files with `.jpg` extension.

    Exclamation mark ! is used to negate the pattern, e.g. `["*.jpg", "!main.jpg"]`
    excludes all `.jpg` files except `main.jpg`.

    **`cp-exclude-from-files`**

    Default value for `neuro cp --exclude-from-files=XXX` option.

    The value is a list of filenames that contain patterns for exclusion files
    and directories from uploading. For every proceeded folder
    patterns from matched exclusion files (e.g. ".neuroignore")
    are read and recursively applied to the directory content.

    Default is `[".neuroignore"]`.

    The format of files is the same as the format of `.gitignore` files:
    every line contains a pattern, exclamation mark `!` is used to negate
    the pattern, empty lines and lines which start with `#` are ignored.

    `[disk]` section
    ----------------

    A section for `neuro disk` command group settings.

    **`life-span`**

    Default disk lifetime limit for `neuro disk create --life-span=XXX` option.

    The value is a string in format `1d2h3m4s` (this example will set the limit to
    1 day, 2 hours, 3 minutes and 4 seconds). Some values can be missing, for example:
    `1d6h`, `30m`. No spaces are allowed between values.

    *Example:*
    ```
      # jobs section
      [job]
      ps-format = "{id;max=30}, {status;max=10}"
      life-span = "1d6h"

      # storage section
      [storage]
      cp-exclude = ["*.jpg", "!main.jpg"]
      cp-exclude-from-files = [".neuroignore", ".gitignore"]

      # jobs section
      [disk]
      life-span = "7d"
    ```

    """


@topics.command()
async def aliases() -> None:
    """\
    Custom command aliases
    ======================

    Aliases exist to provide for abbreviating a system command,
    or for adding default arguments to a regularly used command.

    Aliases are described in user-config files
    (see `neuro help user-config` for details).

    `~/.neuro/user.toml` is used for **global** aliases,
    `.neuro.toml` can be used for saving **project-specific** aliases.
    Project aliases everrides global ones if the same alias
    name exists in both configuration files.

    There are **internal** and **external** aliases.
    An **internal** alias executes built-in neuro command in-place, an **
    external** alias executes any **system OS** command.

    Internal alias
    --------------

    The internal alias is used for running existing neuro CLI command under
    a different name and with optional overriden defaults (passed predefined
    command-line options and arguments).

    For example, the following alias definition makes `neuro lsl` command
    that executes `neuro storage ls -hl` for listing the storage content
    using a long output mode with human-readable file sizes.

    ```
      [alias.lsl]
      cmd = "ls -l --human-readable"
      help = "List directory contents in a long mode.
    ```

    Available configuration arguments:

    * `[alias.lsl]`: defines a subgroup for named alias,
                       `lsl` in this case.
    * `cmd`: command to execute with provided overridden options,
      the key is **mandatory**.
      `cmd` key in alias section implies **internal alias** mode.
    * `help`: help string, displayed by `neuro du --help`
      command (optional),

    Internal allases accept additional command line options and agruments,
    these parameters are passed to underlying command as is.

    E.g., `neuro lsl storage:directory` works as
    `neuro ls -l --human-readable storage:directory`


    External alias
    --------------

    The external alias spawns a subprocess with passing default options and
    arguments, all user-provided arguments are passed to underlying
    programm as well.

    For example, the following configuration defines `neuro du` command as
    an alias for system `du --human-readable` with optional providing the
    directory for analyzing.

    ```
      [alias.du]
      exec = "du"
      args = "[FILE]..."
      options = [
        "-h, --human-readable   print sizes in powers of 1024 (e.g., 1023M)",
        "-d, --max-depth=N  max recursion level for subdirectories lookup",
      ]
      help = '''
        Summarize disk usage of the set of FILEs,
        recursively for directories.
      '''
    ```

    Available configuration arguments:

    * `[alias.du]`: defines a subgroup for named alias,
      `du` in this case.
    * `exec`: external command to execute, the key is **mandatory**.
      `exec` key in alias section implies **external alias** mode.
    * `args`: positional args accepted by the alias,
      the format is described below (optional).
    * `options`: options and flags accepted by the alias,
      the format is described below (optional).
    * `help`: help string, displayed by `neuro lsl --help`
      command (optional),

    **args** is string with sequence of arguments, e.g. `DIR SRC... [DST]`

    If an argument is enclosed in brackets it is **optional** (`[FILE]`).
    If an argument is ended with ellipsis the argument accepts
    multiple values (`SRC...`)

    **options** is a list of strings, a string per option.

    Each string describes a single option, the options definition is separated
    from the option description (help) by two or more spaces.

    The option definition can contain:
    * short name (`-h`)
    * long name (`--human-readable`)
    * indication for required value (`-d, --max-depth=N`).
      If the required value indicator (`=NAME`) is absent
      the option is considered as boolean flag.

    **exec** defines an external system to execute.

    The command is spawn in a subprocess, Neuro CLI waits for the subprocess
    finish, and, in turn, returns the exit code to the outer caller.

    The parameter may specify and executable file along with some options,
    e.g. `exec = "du --human-readable"` enforces human-readable mode
    for `du` command.

    `exec` can be used in **simplified** and **pattern** mode.

    Pattern mode
    ------------

    In **pattern mode** the system command is used along with **substitutions**,
    e.g. `exec = "du {human_readable} {max_depth} {file}"`.
    Substitution is a variable name to expand enclosed in figure brackets,
    e.g. `{file}`.

    It is expanded with an option or positional argument specified
    by `args` or `options`.  The substitution name is automatically lowercased,
    minus (`-`) is replaced with underscore (`_`).
    E.g. `args = "ARG-NAME"` matches to `{arg_name}`.

    If the substitution corresponds to optional parameter and it is not provided
    by user the substitution is expanded to empty string.

    If the substitution corresponds to multiple values all of them are provided,
    e.g. `neuro du folder1 folder2` expands to `du folder1 folder2` since
    `[FILE]...` argument matches to `folder1 folder2` values.

    Options are expanded using longest form if provided,
    e.g. `neuro du -h` is expanded to `du --human-readable`.

    Options with values are expanded as well,
    e.g. `neuro du -d 1` is expanded to `du --max-depth 1`,
    `neuro du --max-depth 1` matches to the same command.

    Simplified mode
    ---------------

    In **simplified mode** the `exec` value does not contain any **substitutions**.
    In this case all parsed `options` and `args` are appended
    to executed command automatically if provided,
    e.g. `exec = "du"` is expanded to
    `exec = "du {human_readable} {max_depth} {file}"`

    """


@topics.command()
async def secrets() -> None:
    """
    Using secrets
    =============

    Secret is a named encrypted data stored in the Neuro Platform Cluster.

    A user can create a secret, list available secret names and delete unused secrets
    but the reading of secret's data back is forbidden.  Instead of bare reading,
    secrets can be accessed from a running job as environment variable or mounted
    file.

    Secrets are isolated and user-specific, a secret that belongs to user A cannot be
    accessed by user B.

    Secrets management
    ------------------

    Use `neuro secret` command group for managing secrets.

    `neuro secret ls` prints all available secret names.

    `neuro secret add key value` creates a secret named *key* with encrypted data
    *value*.

    To store the file's content as a secret please use
    `neuro secret add KEY_NAME @path/to/file.txt` notation.

    `neuro secret rm key` removes the secret *key*.

    Internally, Neuro Platform uses Kubernetes Cluster secrets subsystem a secrets
    storage.

    Secrets usage
    -------------

    As said above, you cannot read a secret directly but should pass it into a running
    job as an environment variable or mounted file.

    To pass a secret *key* as environment variable please use `secret:key` as a value,
    e.g. `neuro run --env VAR=secret:key ...` form.

    To mount a secret as a file please use `secret:` volume's schema, e.g.
    `neuro run --volume secret:key:/mount/path/file.txt`.

    """


@topics.command()
async def sharing() -> None:
    """
    Using sharing functionality
    ===========================

    Understanding permissions
    -------------------------
    Neu.ro platform supports five levels of access:
    * deny - no access
    * list - permits listing entities, but not looking at their details
    * read - read-only access to entity
    * write - read-write access (including deletion) to entity
    * manage - allows modification of entity's permissions

    Please note permissions are inclusive: write permission implies read and manage
    includes read and write, and so on.

    Permissions can be granted via `neuro acl grant` or `neuro share` and
    revoked via `neuro acl revoke`:
    ```
    neuro acl grant job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
    neuro acl revoke job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
    ```

    You can check entities owned by you and shared with you by others by running
    `neuro acl list`. This will show all entity URIs and their access levels.
    If you want to focus on a subset of entities you can filter them with `-s`.
    For instance, `neuro acl list -s job` will only show you jobs you have access to.

    If `neuro acl list` output contains a URI, such as `secret:` or `storage:`
    it means you've got corresponding permission for all entities of that type.

    Running `neuro acl list --shared` will show you entities shared by you
    along with users/roles you shared them with.

    Roles
    -----
    Neu.ro platform supports role-based access control. Role is a packed set
    of permissions to multiple entities which can be shared together. There's several
    default roles in each cluster, plus users may create their own custom roles.

    Default roles are:
    * {cluster}/manager
    * {cluster}/admin
    * {cluster}/users/{username} - such roles are created for every cluster user and
        always contain a whole set of user's permissions.

    If you want to create a new role, run
    `neuro acl add-role {username}/roles/{rolename}`

    This will create a role "rolename" with empty permission set. Then you may share
    resources with the new role via `neuro acl grant`:

    ```
    neuro acl grant image:IMAGE_NAME {username}/roles/{rolename}
    neuro acl grant job:JOB_NAME {username}/roles/{rolename}
    neuro acl grant job:ANOTHER_JOB_NAME {username}/roles/{rolename}
    neuro acl grant storage:/folder_name {username}/roles/{rolename}
    ```

    When ready, grant this permission set to another user (`bob` in the example):

    ```
    neuro acl grant role://{username}/roles/{rolename} bob
    ```

    From now on, `bob` will have access to all entities listed under
    the `{username}/roles/{rolename}` role. The list can be viewed by
    `neuro acl list -u {username}/roles/{rolename}`.

    If needed, role can be revoked:
    `neuro acl revoke role://{username}/roles/{rolename} bob`

    And deleted by running `neuro acl remove-role {username}/roles/{rolename}`.
    """
