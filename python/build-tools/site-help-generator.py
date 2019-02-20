#!/usr/bin/env python3

import re
import sys
from pathlib import Path

import click

from neuromation.cli.main import cli


HERE = Path(sys.argv[0]).resolve().parent


def write_meta(meta, out):
    out.append("---")
    for key, val in meta.items():
        out.append(f'{key}: "{val}"')
    out.append("---")
    out.append("")


def gen_command(index, index2, cmd, target_path, parent_ctx):
    out = []
    with click.Context(cmd, parent=parent_ctx, info_name=cmd.name) as ctx:
        category = parent_ctx.command.name
        if category == "cli":
            category = "shortcuts"
        meta = {
            "title": ctx.command_path,
            "short_title": cmd.name,
            "category": category,
            "path": "/" + category + "/" + cmd.name,
            "index": "true",
        }
        write_meta(meta, out)

        out.append(cmd.get_short_help_str())
        out.append("")

        out.append("### Usage")
        out.append("```bash")
        pieces = cmd.collect_usage_pieces(ctx)
        out.append(f"neuro {cmd.name} " + " ".join(pieces))
        out.append("```")
        out.append("")

        out.append(click.unstyle(cmd.help))
        out.append("")

        opts = []
        w1 = w2 = 0
        for param in cmd.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is None:
                continue
            name, descr = rv

            # durty code for wrapping options with backticks
            l4 = []
            l1 = re.split(" ?/ ?", name)
            for part in l1:
                l2 = re.split(" ?, ?", part)
                l4.append(", ".join(["`" + part2 + "`" for part2 in l2]))

            name2 = " / ".join(l4)

            w1 = max(w1, len(name2))
            w2 = max(w2, len(descr))
            opts.append((name2, descr))

        name_title = "Name".ljust(w1)
        descr_title = "Description".ljust(w2)
        name_sep = "-" * w1
        descr_sep = "-" * w2

        out.append("### Options")
        out.append("")
        out.append(f"| {name_title} | {descr_title} |")
        out.append(f"| {name_sep} | {descr_sep} |")

        for name, descr in opts:
            name = name.ljust(w1)
            descr = descr.ljust(w2)
            out.append(f"| {name} | {descr} |")

        fname = target_path / f"{index:02d}_{index2:02d}__{cmd.name}.md"
        fname.write_text("\n".join(out))


def gen_group(index, group, target_path, parent_ctx):
    out = []
    with click.Context(group, parent=parent_ctx, info_name=group.name) as ctx:
        meta = {
            "title": " ".join(["neuro", group.name]),
            "short_title": group.name,
            "category": group.name,
            "path": "/" + group.name,
            "index": "true",
        }
        write_meta(meta, out)

        out.append(group.get_short_help_str())
        out.append("")

        out.append("### Usage")
        out.append("```bash")
        pieces = group.collect_usage_pieces(ctx)
        out.append(f"neuro {group.name} " + " ".join(pieces))
        out.append("```")
        out.append("")

        out.append(click.unstyle(group.help))
        out.append("")

        commands = []
        for cmd_name in group.list_commands(ctx):
            cmd = group.get_command(ctx, cmd_name)
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            commands.append(cmd)

        out.append("### Commands")
        out.append("")
        for cmd in commands:
            out.append(
                f"- [neuro {group.name} {cmd.name}](/{group.name}/{cmd.name}): "
                f"{cmd.get_short_help_str()}"
            )

        fname = target_path / f"{index:02d}_00__{group.name}.md"
        fname.write_text("\n".join(out))

        for index2, cmd in enumerate(commands, 1):
            gen_command(index, index2, cmd, target_path, ctx)


def gen_shortcuts(index, commands, target_path, ctx):
    out = []
    meta = {
        "title": "shortcuts",
        "path": "/shortcuts",
        "category": "shortcuts",
        "index": "true",
    }
    write_meta(meta, out)

    out.append("### Shortcuts")
    out.append("")

    for cmd in commands:
        out.append(f"- [neuro {cmd.name}](/{cmd.name}): " f"{cmd.get_short_help_str()}")

    fname = target_path / f"{index:02d}_00__shortcuts.md"
    fname.write_text("\n".join(out))

    for index2, cmd in enumerate(commands, 1):
        gen_command(index, index2, cmd, target_path, ctx)


@click.command()
@click.option(
    "--target-dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True
    ),
    help="Target dir in platform-web project",
    default=str(HERE.parent.parent.parent / "platform-web/docs"),
    show_default=True,
)
def main(target_dir):
    target_path = Path(target_dir)
    EXCLUDES = ("00",)
    for child in target_path.iterdir():
        if child.name.startswith(EXCLUDES):
            continue
        child.unlink()

    groups = []
    shortcuts = []
    with click.Context(
        cli, info_name="neuro", color=False, terminal_width=80, max_content_width=80
    ) as ctx:
        for cmd_name in cli.list_commands(ctx):
            cmd = cli.get_command(ctx, cmd_name)
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            if cmd.name == "help":
                continue

            if isinstance(cmd, click.MultiCommand):
                groups.append(cmd)
            else:
                shortcuts.append(cmd)

    for i, group in enumerate(groups, 1):
        gen_group(i, group, target_path, ctx)

    gen_shortcuts(i + 1, shortcuts, target_path, ctx)


if __name__ == "__main__":
    main()
