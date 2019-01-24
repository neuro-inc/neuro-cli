#!/usr/bin/env python

import os
import re
import sys
from dataclasses import dataclass, field
from textwrap import dedent
from typing import Any, List

import click

from neuromation.cli.main import cli


@dataclass()
class Option:
    pattern: str = None
    description: str = None


@dataclass()
class CommandInfo:
    name: str = None
    usage: str = None
    short: str = None
    description: str = None
    options: List[Option] = field(default_factory=list)
    examples: str = None
    children: List[Any] = field(default_factory=list)  # CommandInfo


def parse_doc(ctx, command, stack) -> CommandInfo:
    name = ' '.join(stack)
    formatter = ctx.make_formatter()
    command.format_usage(ctx, formatter)
    usage = formatter.getvalue()
    usage = re.split(r"usage\s*:", usage, maxsplit=2, flags=re.IGNORECASE)[1].strip()
    short = command.get_short_help_str(80)
    info = CommandInfo(name=name, usage=usage, short=short)

    formatter = ctx.make_formatter()
    command.format_help_text(ctx, formatter)
    help = formatter.getvalue()
    parts = re.split(r"examples:", help, flags=re.IGNORECASE)
    info.description = dedent(parts[0])
    if len(parts) > 1:
        assert len(parts) == 2
        info.examples = dedent(parts[1])

    for param in command.get_params(ctx):
        ret = param.get_help_record(ctx)
        if ret:
            info.options.append(Option(ret[0], ret[1]))

    return info


def parse_command(parent_ctx, command, stack) -> CommandInfo:
    """
    Walk given command and all subcommands and create corresponding CommandInfo
    """

    with click.Context(
        command,
        info_name=stack[-1],
        color=False,
        terminal_width=80,
        max_content_width=80,
        parent=parent_ctx,
    ) as ctx:
        info = parse_doc(ctx, command, stack)

        if isinstance(command, click.MultiCommand):
            for command_name in command.list_commands(ctx):
                info.children.append(
                    parse_command(
                        ctx,
                        command.get_command(ctx, command_name),
                        stack + [command_name],
                    )
                )

    return info


def generate_markdown(info: CommandInfo, header_prefix: str = "#") -> str:
    def simple_escape_line(text: str) -> str:
        escaped = re.sub(r"\*(\S[^*]*)\*", r"\\*\1*", text)
        escaped = re.sub(r"\-(\S[^*]*)\-", r"\\-\1-", escaped)
        escaped = re.sub(r"\_(\S[^*]*)\_", r"\\_\1_", escaped)
        escaped = re.sub(r"\[(\S[^\]]*)\]", r"\\[\1]", escaped)
        escaped = re.sub(r"\((\S[^)]*)\)", r"\\(\1)", escaped)

        return escaped

    def escape(text: str) -> str:
        # escaped = text.replace('\\', '\\\\')
        escaped = []
        lines = text.splitlines()
        for line in lines:
            before = line
            after = simple_escape_line(line)
            while before != after:
                before = after
                after = simple_escape_line(line)
            escaped.append(after)
        return "<br/>".join(escaped)

    md = ""
    md += f"{header_prefix}# {info.name}"
    md += "\n\n"

    if info.description:
        md += escape(info.description)
        md += "\n\n"

    if info.usage:
        md += f"**Usage:**\n\n"
        md += "```bash\n"
        md += info.usage
        md += "\n```\n\n"

    if info.examples:
        md += f"**Examples:**\n\n"
        md += "```bash\n"
        md += info.examples
        md += "\n```\n\n"

    if info.options:
        md += "**Options:**\n\n"
        md += "Name | Description|\n"
        md += "|----|------------|\n"
        for option in info.options:
            md += f"|_{escape(option.pattern)}_|{escape(option.description)}|\n"

        md += "\n\n"

    if info.children:
        md += "**Commands:**\n\n"

        for child in info.children:
            anchor = child.name
            anchor = "#" + anchor.replace(" ", "-")
            md += f"* _[{child.name}]({anchor})_: {child.description}"

        md += "\n\n"

    return md


def generate_command_markdown(info: CommandInfo, header_prefix="") -> str:
    md = generate_markdown(info, header_prefix)
    if info.children:
        md += "\n\n" + "\n\n".join(
            generate_command_markdown(sub_command, header_prefix + "#")
            for sub_command in info.children
        )
    return md


def main():
    if len(sys.argv) != 3:
        print("Usage cli-help-generator.py input_file output_file")
        exit(os.EX_USAGE)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_file, "r") as input:
        with open(output_file, "w") as output:
            template = input.read()
            info = parse_command(None, cli, ["neuro"])
            cli_doc = generate_command_markdown(info, "")
            generated_md = template.format(cli_doc=cli_doc)
            output.write(generated_md)


if __name__ == "__main__":
    main()
