import abc
from typing import Dict

import click

from neuromation.api import (
    AbstractDockerImageProgress,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
)
from neuromation.api.abc import (
    ImageCommitFinished,
    ImageCommitStarted,
    ImageProgressSave,
)
from neuromation.cli.printer import StreamPrinter, TTYPrinter


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
        cnt = click.style(self._shorten_container_hash(data.container), bold=True)
        self._printer.print(f"Creating image {img} from container {cnt}")

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
        container = self._shorten_container_hash(data.container)
        self._printer.print(f"Creating image from container '{container}'...")

    def commit_finished(self, data: ImageCommitFinished) -> None:
        self._printer.print("Image created")

    def close(self) -> None:
        self._printer.close()
