import abc
from typing import Dict, Iterable

import click

from neuromation.api import (
    AbstractDockerImageProgress,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
    RemoteImage,
)
from neuromation.api.abc import (
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressSave,
)
from neuromation.cli.printer import StreamPrinter, TTYPrinter

from .ftable import table
from .utils import ImageFormatter


class DockerImageProgress(AbstractDockerImageProgress):
    @classmethod
    def create(cls, tty: bool, quiet: bool) -> "DockerImageProgress":
        if quiet:
            progress: DockerImageProgress = QuietDockerImageProgress()
        elif tty:
            progress = DetailedDockerImageProgress()
        else:
            progress = StreamDockerImageProgress()
        return progress

    @abc.abstractmethod
    def close(self) -> None:  # pragma: no cover
        pass

    def _shorten_container_hash(self, container: str) -> str:
        return container[:12]


class QuietDockerImageProgress(DockerImageProgress):
    def pull(self, data: ImageProgressPull) -> None:
        pass

    def push(self, data: ImageProgressPush) -> None:
        pass

    def step(self, data: ImageProgressStep) -> None:
        pass

    def close(self) -> None:
        pass

    def save(self, data: ImageProgressSave) -> None:
        pass

    def commit_started(self, data: ImageCommitStarted) -> None:
        pass

    def commit_finished(self, data: ImageCommitFinished) -> None:
        pass


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self) -> None:
        self._mapping: Dict[str, int] = {}
        self._printer = TTYPrinter()

    def push(self, data: ImageProgressPush) -> None:
        src = click.style(str(data.src), bold=True)
        dst = click.style(str(data.dst), bold=True)
        self._printer.print(f"Pushing image {src} => {dst}")

    def pull(self, data: ImageProgressPull) -> None:
        src = click.style(str(data.src), bold=True)
        dst = click.style(str(data.dst), bold=True)
        self._printer.print(f"Pulling image {src} => {dst}")

    def step(self, data: ImageProgressStep) -> None:
        if data.layer_id:
            if data.layer_id in self._mapping.keys():
                lineno = self._mapping[data.layer_id]
                self._printer.print(data.message, lineno)
            else:
                self._mapping[data.layer_id] = self._printer.total_lines
                self._printer.print(data.message)
        else:
            self._printer.print(data.message)

    def save(self, data: ImageProgressSave) -> None:
        job = click.style(str(data.job), bold=True)
        dst = click.style(str(data.dst), bold=True)
        self._printer.print(f"Saving {job} -> {dst}")

    def commit_started(self, data: ImageCommitStarted) -> None:
        img = click.style(str(data.target_image), bold=True)
        self._printer.print(f"Creating image {img} image from the job container")

    def commit_finished(self, data: ImageCommitFinished) -> None:
        self._printer.print("Image created")

    def close(self) -> None:
        self._printer.close()


class StreamDockerImageProgress(DockerImageProgress):
    def __init__(self) -> None:
        self._printer = StreamPrinter()

    def push(self, data: ImageProgressPush) -> None:
        self._printer.print(f"Using local image '{data.src}'")
        self._printer.print(f"Using remote image '{data.dst}'")
        self._printer.print("Pushing image...")

    def pull(self, data: ImageProgressPull) -> None:
        self._printer.print(f"Using remote image '{data.src}'")
        self._printer.print(f"Using local image '{data.dst}'")
        self._printer.print("Pulling image...")

    def step(self, data: ImageProgressStep) -> None:
        if data.layer_id:
            self._printer.tick()
        else:
            self._printer.print(data.message)

    def save(self, data: ImageProgressSave) -> None:
        self._printer.print(f"Saving job '{data.job}' to image '{data.dst}'...")

    def commit_started(self, data: ImageCommitStarted) -> None:
        self._printer.print(f"Using remote image '{data.target_image}'")
        self._printer.print(f"Creating image from the job container...")

    def commit_finished(self, data: ImageCommitFinished) -> None:
        self._printer.print("Image created")

    def close(self) -> None:
        self._printer.close()


class BaseImagesFormatter:
    def __init__(self, image_formatter: ImageFormatter) -> None:
        self._format_image = image_formatter

    @abc.abstractmethod
    def __call__(self, images: Iterable[RemoteImage]) -> Iterable[str]:
        raise NotImplementedError


class ShortImagesFormatter(BaseImagesFormatter):
    def __call__(self, images: Iterable[RemoteImage]) -> Iterable[str]:
        return (
            click.style(self._format_image(image), underline=True) for image in images
        )


class LongImagesFormatter(BaseImagesFormatter):
    def __call__(self, images: Iterable[RemoteImage]) -> Iterable[str]:
        header = [
            click.style("Neuro URL", bold=True),
            click.style("Docker URL", bold=True),
        ]
        rows = [
            [
                click.style(self._format_image(image), underline=True),
                click.style(image.as_docker_url(with_scheme=True), underline=True),
            ]
            for image in images
        ]
        return table([header] + rows)
