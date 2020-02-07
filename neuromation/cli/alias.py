import ast
import re
import shlex
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set

import click

from neuromation.api import ConfigError

from .root import Root
from .utils import NeuroClickMixin


class InternalAlias(NeuroClickMixin, click.Command):
    ignore_unknown_options = True
    allow_interspersed_args = False
    allow_extra_args = True

    def __init__(self, name: str, alias: Dict[str, str]) -> None:
        super().__init__(name,)
        assert "cmd" in alias
        self.alias = alias

    def invoke(self, ctx: click.Context) -> None:
        parent = ctx.parent
        assert parent is not None
        sub_cmd, *sub_args = shlex.split(self.alias["cmd"])
        parent_cmd = parent.command
        assert isinstance(parent_cmd, click.MultiCommand)
        cmd = parent_cmd.get_command(parent, sub_cmd)
        if cmd is None:
            ctx.fail(f'Alias {self.name} refers to unknown command "{sub_cmd}"')
        with ctx:  # type: ignore
            ctx.invoked_subcommand = self.name
            sub_ctx = cmd.make_context(self.name, sub_args + ctx.args, parent=ctx)
            with sub_ctx:  # type: ignore
                sub_ctx.command.invoke(sub_ctx)

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        self.format_usage(ctx, formatter)
        formatter.write_paragraph()
        assert ctx.parent is not None
        alias_cmd = self.alias["cmd"]
        formatter.write(
            "Alias for "
            + click.style(f'"{ctx.parent.info_name} {alias_cmd}"', bold=True)
        )
        formatter.write_paragraph()

        help = self.alias.get("help")
        if help is not None:
            formatter.write("\n")
            formatter.write_text(help)

        self.format_options(ctx, formatter)


class ExternalAlias(NeuroClickMixin, click.Command):
    ignore_unknown_options = True
    allow_interspersed_args = False
    allow_extra_args = True

    def __init__(self, name: str, alias: Dict[str, Any]) -> None:
        assert "exec" in alias
        options = _parse_options(alias.get("options", ""))
        args = _parse_args(alias.get("args", ""))
        _validate_exec(
            alias["exec"],
            {param.name for param in options},
            {param.name for param in args},
        )
        super().__init__(name, params=options + args)
        self.alias = alias

    def invoke(self, ctx: click.Context) -> None:
        cmd = self.alias["exec"]
        matches = re.findall(r"{\w+}", cmd)
        replaces = {}
        for match in matches:
            name = match[1:-1]  # drop curly brackets

            for param in self.params:
                if param.name == name:
                    break
            else:  # pragma: no cover
                # Unreachable code, _validate_exec()
                # makes sure that all param names are handled
                raise ConfigError(f'Unknown parameter {name} in "{cmd}"')

            if isinstance(param, click.Argument):
                val = ctx.params[name]
                if not param.required:
                    if val is None:
                        replaces[match] = ""
                        continue
                if param.nargs != 1:
                    val = " ".join(val)
                replaces[match] = val
            elif isinstance(param, click.Option):
                val = ctx.params[name]
                if param.is_flag:
                    # parser generates bool flags only
                    assert param.is_bool_flag
                    if not val:
                        # empty tuple
                        replaces[match] = ""
                        continue
                    vals = []
                    for item in val:
                        if val:
                            vals.append(_longest(param.opts))
                        else:
                            vals.append(_longest(param.secondary_opts))
                    replaces[match] = " ".join(vals)
                else:
                    if not val:
                        # empty tuple
                        replaces[match] = ""
                    else:
                        vals = []
                        for item in val:
                            vals.append(f"{_longest(param.opts)} {item}")
                        replaces[match] = " ".join(vals)
            else:  # pragma: no cover
                # Unreachable branch
                raise RuntimeError(f"Unsupported parameter type {type(param)}")
        for name, val in replaces.items():
            cmd = cmd.replace(name, val)
        ret = subprocess.run(shlex.split(cmd))
        if ret.returncode:
            sys.exit(ret.returncode)

    def format_help_text(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        formatter.write_paragraph()
        alias_cmd = self.alias["exec"]
        formatter.write_text("Alias for " + click.style(f'"{alias_cmd}"', bold=True))

        help = self.alias.get("help")
        if help is not None:
            formatter.write("\n")
            formatter.write_text(help)


async def find_alias(
    ctx: click.Context, cmd_name: str, args: List[str], root: Root
) -> Optional[click.Command]:
    client = await root.init_client()
    config = await client.config.get_user_config()
    alias = config.get("alias", {}).get(cmd_name)
    if alias is None:
        # Command not found
        return None
    if "cmd" in alias:
        return InternalAlias(cmd_name, alias)
    elif "exec" in alias:
        return ExternalAlias(cmd_name, alias)
    else:  # pragma: no cover
        # This branch is unreachable,
        # Config file validator should prevent unknown alias type
        ctx.fail(f"Invalid alias description type for {cmd_name}")


def _parse_options(descr: List[str]) -> List[click.Parameter]:
    ret = []
    for od in descr:
        opts = []
        is_flag = True
        options, _, description = od.strip().partition("  ")
        options = options.replace(",", " ").replace("=", " ")
        for s in options.split():
            if s.startswith("--"):
                if not s[2:].replace("-", "_").isidentifier():
                    raise ConfigError(f"Cannot parse option {od}")
                opts.append(s)
            elif s.startswith("-"):
                if not s[1:].isidentifier():
                    raise ConfigError(f"Cannot parse option {od}")
                opts.append(s)
            else:
                is_flag = False
        description = description.strip()
        matched = re.findall(r"\[default: (.*)\]", description, flags=re.I)
        if matched:
            default = ast.literal_eval(matched[0])
        else:
            default = None
        ret.append(
            click.Option(
                opts, is_flag=is_flag, default=default, multiple=True, help=description
            )
        )
    return ret  # type: ignore


def _parse_args(source: str) -> List[click.Parameter]:
    ret = []
    src1 = re.sub(r"([\[\]]|\.\.\.)", r" \1 ", source)
    src2 = [s for s in re.split(r"\s+|(\S*<.*?>)", src1) if s]
    required = True
    multiple = False
    brackets = False
    arg = None
    for item in src2:
        if item == "[":
            if brackets:
                raise ConfigError(f'Cannot parse args "{source}", nested brackets')
            brackets = True
        elif item == "]":
            if not brackets:
                raise ConfigError(f'Cannot parse args "{source}", missing open bracket')
            brackets = False
            required = False
        elif item == "...":
            if arg is None:
                raise ConfigError(
                    f'Cannot parse args "{source}", '
                    "ellipsis should follow an argument"
                )
            if brackets:
                raise ConfigError(
                    f'Cannot parse args "{source}", put ellipsis outside or brackets'
                )
            multiple = True
        else:
            if arg is not None:
                if brackets:
                    raise ConfigError(
                        f'Cannot parse args "{source}", missing close bracket'
                    )
                ret.append(
                    click.Argument(
                        [arg],
                        required=required,
                        nargs=-1 if multiple else 1,
                        type=click.UNPROCESSED,
                    )
                )
                required = True
                multiple = False
                brackets = False
                arg = None
            arg = item
            if not arg.isupper():
                raise ConfigError(
                    f'Cannot parse args "{source}", '
                    f"Argument name {arg} should be uppercased"
                )
    if arg is not None:
        if brackets:
            raise ConfigError(f'Cannot parse args "{source}", ' "missing close bracket")
        ret.append(
            click.Argument(
                [arg],
                required=required,
                nargs=-1 if multiple else 1,
                type=click.UNPROCESSED,
            )
        )
    return ret  # type: ignore


def _validate_exec(cmd: str, options: Set[str], args: Set[str]) -> None:
    if args & options:
        overlapped = ",".join(args & options)
        raise ConfigError(
            "The following names are present in both "
            f"positional and optional arguments: {overlapped}"
        )
    params = args | options
    matches = re.findall(r"{\w*}", cmd)
    for match in matches:
        name = match[1:-1]  # drop curly brackets
        if not name:
            raise ConfigError(f"Empty substitution is not allowed")

        if not name.islower():
            raise ConfigError(f"Parameter {name} should be lowercased")

        if not name.isidentifier():
            raise ConfigError(f"Parameter {name} is not a walid identifier")

        if name not in params:
            raise ConfigError(f'Unknown parameter {name} in "{cmd}"')


def _longest(opts: List[str]) -> str:
    # group long options first
    possible_opts = sorted(opts, key=lambda x: -len(x))
    return possible_opts[0]
