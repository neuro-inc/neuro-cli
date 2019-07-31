import abc
from typing import Dict

from neuromation.api import (
    AbstractDockerImageProgress,
    ImageProgressPull,
    ImageProgressPush,
    ImageProgressStep,
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
    def close(self) -> None:
        pass


class QuietDockerImageProgress(DockerImageProgress):
    def pull(self, data: ImageProgressPull) -> None:
        pass

    def push(self, data: ImageProgressPush) -> None:
        pass

    def step(self, data: ImageProgressStep) -> None:
        pass

    def close(self) -> None:
        pass


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self) -> None:
        self._mapping: Dict[str, int] = {}
        self._printer = TTYPrinter()

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
            if data.layer_id in self._mapping.keys():
                lineno = self._mapping[data.layer_id]
                self._printer.print(data.message, lineno)
            else:
                self._mapping[data.layer_id] = self._printer.total_lines
                self._printer.print(data.message)
        else:
            self._printer.print(data.message)

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

    def close(self) -> None:
        self._printer.close()
