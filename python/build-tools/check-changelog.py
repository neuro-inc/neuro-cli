#!/usr/bin/env python3

import pathlib

import click


@click.command()
@click.argument("file", type=click.Path(exists=True, file_okay=True, readable=True))
@click.pass_context
def main(ctx, file):
    path = pathlib.Path(file)
    body = path.read_text()
    lines = [l.strip() for l in body.splitlines()]
    if lines:
        ctx.exit(0)
    else:
        click.echo(f"The file {file} is empty.")
        ctx.exit(1)
