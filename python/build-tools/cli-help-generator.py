#!/usr/bin/env python

import os
import re
import sys
from dataclasses import dataclass, field
from textwrap import dedent
from typing import Any, List

import docopt

from neuromation.cli.commands import commands, help_format, normalize_options, parse
from neuromation.cli.main import DEFAULTS, neuro


@dataclass()
class ArgumentValue:
    name: str
    description: str = None


@dataclass()
class Argument:
    name: str
    values: List[ArgumentValue] = field(default_factory=list)


@dataclass()
class Option:
    pattern: str
    description: str = None


@dataclass()
class CommandInfo:
    name: str
    usage: str = None
    description: str = None
    options: List[Option] = field(default_factory=list)
    examples: str = None
    children: List[Any] = field(default_factory=list)  # CommandInfo
    arguments: List[Argument] = field(default_factory=list)


def parse_doc(doc, name=None) -> CommandInfo:
    usage = docopt.printable_usage(doc)
    parts = re.split(r"usage\s*:", usage, maxsplit=2, flags=re.IGNORECASE)
    usage = parts[1].strip()
    if not name:
        name = usage
    info = CommandInfo(name=name, usage=parts[1].strip())
    parts = doc.split(info.usage, 2)
    remains = parts[1]
    remains = dedent(remains)
    lines = remains.splitlines(True)
    mode = "description"
    description = []
    examples = []
    argument = None
    argument_value = None
    argument_value_ident = None
    option = None
    for line in lines:
        if not line.strip():
            continue
        # it`s like as option
        if re.match(r"^\s*-[-\w\d]+", line):
            mode = "options"
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=2)
            option = Option(pattern=parts[0])
            if len(parts) == 2:
                option.description = parts[1].strip()
            info.options.append(option)
        # just options block, special case
        elif re.match(r"options:\s*", line, flags=re.IGNORECASE):
            mode = "options"
        # examples block
        elif re.match(r"example(?:s){0,1}:\s*", line, flags=re.IGNORECASE):
            mode = "examples"
        # like as argument section
        elif re.fullmatch(r"\w+:\s*", line):
            match = re.match(r"(\w+):\s*", line)
            argument = Argument(name=match.group(1))
            info.arguments.append(argument)
            mode = "arguments"
            argument_value_ident = None
        elif mode == "description":
            description.append(line.strip())
        elif mode == "examples":
            examples.append(line.strip())
        elif mode == "option":
            description.append(line.strip())
        elif mode == "arguments":
            ident = len(line) - len(line.lstrip())
            match = re.match(r"\s*(\w+)\s*(.+)*", line)
            if match and (
                argument_value_ident == ident or argument_value_ident is None
            ):
                argument_value = ArgumentValue(
                    name=match.group(1), description=match.group(2).strip()
                )
                argument.values.append(argument_value)
                argument_value_ident = ident
            elif argument_value:
                argument_value.description += "\n" + line.strip()
    if examples:
        info.examples = "\n".join(examples)
    if description:
        info.description = "\n".join(description)

    return info


def parse_command(command, format_spec, stack) -> CommandInfo:
    """
    Walk given command and all subcommands and create corresponding CommandInfo
    """

    name = " ".join(stack)
    doc = command.__doc__
    if not doc:
        return CommandInfo(name=name, description="Not implemented")

    doc = help_format(doc, format_spec)
    info = parse_doc(doc, name)
    try:
        options, _ = parse(doc, stack)
        command_result = command(**{**normalize_options(options, ["COMMAND"])})
    except docopt.DocoptExit:
        # dead end
        if not re.search(r"\sCOMMAND\s*$", doc, re.M):
            return info
        # Try execute command without options
        command_result = command()

    if command_result:
        for command_name in commands(command_result):
            info.children.append(
                parse_command(
                    command_result.get(command_name),
                    format_spec,
                    stack + [command_name],
                )
            )
    return info


def generate_markdown(info: CommandInfo, header_prefix: str = "#") -> str:
    def fix_eol(text):
        return re.sub(r"[\n\r]+", "\n\n", text)

    md = ""
    md += f"{header_prefix}# {info.name}"
    md += "\n\n"

    if info.description:
        md += info.description
        md += "\n\n"

    if info.usage:
        md += f"**Usage:**\n\n"
        md += "```bash\n"
        md += info.usage
        md += "\n```\n\n"

    if info.options:
        md += "**Options:**\n\n"
        for option in info.options:
            md += f"* _{option.pattern}_: {option.description}\n"
        md += "\n\n"

    for argument in info.arguments:
        md += f"**{argument.name}:**\n\n"
        for value in argument.values:
            if argument.name == "Commands":
                anchor = info.name + " " + value.name
                anchor = "#" + anchor.replace(" ", "-")
                md += f"* _[{value.name}]({anchor})_: {value.description}"
            else:
                md += f"* _{value.name}_: {value.description}"
            md += "\n\n"

    if info.examples:
        md += f"**Examples:**\n\n"
        md += "```bash\n"
        md += info.examples
        md += "\n```\n\n"
    return md


def generate_command_markdown(info: CommandInfo, header_prefix="") -> str:
    md = generate_markdown(info, header_prefix)
    if info.children:
        # Lets find Commands argument for iterationg
        command_args = [
            argument
            for argument in info.arguments
            if argument.name.lower() == "commands"
        ]
        if command_args:
            arg = command_args[0]
            for value in arg.values:
                sub_commands = [
                    sub_command
                    for sub_command in info.children
                    if sub_command.name == info.name + " " + value.name
                ]
                if not sub_commands:
                    raise Exception(
                        f"Children command {value.name} not found in {info.name}"
                    )
                md += "\n\n"
                md += generate_command_markdown(sub_commands[0], header_prefix + "#")
        # Ok, we can iterate sub commands in random order too
        else:
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
    try:
        with open(input_file, "r") as input:
            with open(output_file, "w") as output:
                template = input.read()
                info = parse_command(neuro, DEFAULTS, ["neuro"])
                cli_doc = generate_command_markdown(info, "")
                generated_md = template.format(cli_doc=cli_doc)
                output.write(generated_md)
    except BaseException as error:
        print(error)


if __name__ == "__main__":
    main()
