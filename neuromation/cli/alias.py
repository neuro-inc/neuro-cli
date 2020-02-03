import re
import shlex
from typing import Dict, List, Optional

import click
import docopt

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
            ctx.fail(f"Alias {self.name} refers to unknown command {sub_cmd}")
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
        self.format_options(ctx, formatter)


class ExternalAlias(NeuroClickMixin, click.Command):
    ignore_unknown_options = True
    allow_interspersed_args = False
    allow_extra_args = True

    def __init__(self, name: str, alias: Dict[str, str]) -> None:
        super().__init__(name)
        assert "usage" in alias
        self.alias = alias

    def invoke(self, ctx: click.Context) -> None:
        args = ctx.args
        # extracted from docopt.docopt() and adopted for neuro config format
        options = _parse_defaults(self.alias.get("options"))
        pattern = docopt.parse_pattern(
            docopt.formal_usage(self.alias["usage"]), options
        )
        # [default] syntax for argument is disabled
        # for a in pattern.flat(Argument):
        #     same_name = [d for d in arguments if d.name == a.name]
        #     if same_name:
        #         a.value = same_name[0].value
        argv = docopt.parse_argv(
            docopt.Tokens(args), list(options), options_first=False
        )
        pattern_options = set(pattern.flat(docopt.Option))
        for options_shortcut in pattern.flat(docopt.OptionsShortcut):
            doc_options = _parse_defaults(self.alias.get("options"))
            options_shortcut.children = list(set(doc_options) - pattern_options)
            # if any_options:
            #     options_shortcut.children += [Option(o.short, o.long, o.argcount)
            #                     for o in argv if type(o) is Option]
        matched, left, collected = pattern.fix().match(argv)

        if not matched or left != []:  # better error message if left?
            ctx.fail(f"Cannot parse arguments")
            return Dict((a.name, a.value) for a in (pattern.flat() + collected))
        raise DocoptExit()

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
        self.format_options(ctx, formatter)


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
    elif "usage" in alias:
        return ExternalAlias(cmd_name, alias)
        pass
    else:
        ctx.fail(f"Invalid alias description type for {cmd_name}")


def _parse_defaults(options: List[str]) -> List[docopt.Option]:
    defaults = []
    if options is None:
        return defaults
    for opt in options:
        # FIXME corner case "bla: options: --foo"
        _, _, s = s.partition(":")  # get rid of "options:"
        split = re.split("\n[ \t]*(-\S+?)", "\n" + s)[1:]
        split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
        options = [docopt.Option.parse(s) for s in split if s.startswith("-")]
        defaults += options
    return defaults
