from enum import Enum
from typing import Dict

from neuromation.api import (
    AbstractDockerImageProgress,
    ImageProgressComplete,
    ImageProgressStart,
    ImageProgressStep,
)
from neuromation.cli.printer import StreamPrinter, TTYPrinter


class DockerImageOperation(str, Enum):
    PUSH = "push"
    PULL = "pull"


class DockerImageProgress(AbstractDockerImageProgress):
    @classmethod
    def create(
        cls, type: DockerImageOperation, tty: bool, quiet: bool
    ) -> AbstractDockerImageProgress:
        if quiet:
            progress: AbstractDockerImageProgress = QuietDockerImageProgress(type)
        elif tty:
            progress = DetailedDockerImageProgress(type)
        else:
            progress = StreamDockerImageProgress(type)
        return progress

    def __init__(self, type: DockerImageOperation) -> None:
        self._type = type


class QuietDockerImageProgress(DockerImageProgress):
    def start(self, data: ImageProgressStart) -> None:
        pass

    def step(self, data: ImageProgressStep) -> None:
        pass

    def complete(self, data: ImageProgressComplete) -> None:
        pass


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self, type: DockerImageOperation) -> None:
        super().__init__(type)
        self._mapping: Dict[str, int] = {}
        self._printer = TTYPrinter()

    def start(self, data: ImageProgressStart) -> None:
        if self._type == DockerImageOperation.PUSH:
            self._printer.print(f"Using local image '{data.src}'")
            self._printer.print(f"Using remote image '{data.dst}'")
            self._printer.print("Pushing image...")
        elif self._type == DockerImageOperation.PULL:
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

    def complete(self, data: ImageProgressComplete) -> None:
        self._printer.close()


class StreamDockerImageProgress(DockerImageProgress):
    def __init__(self, type: DockerImageOperation) -> None:
        super().__init__(type)
        self._printer = StreamPrinter()

    def start(self, data: ImageProgressStart) -> None:
        if self._type == DockerImageOperation.PUSH:
            self._printer.print(f"Using local image '{data.src}'")
            self._printer.print(f"Using remote image '{data.dst}'")
            self._printer.print("Pushing image...")
        elif self._type == DockerImageOperation.PULL:
            self._printer.print(f"Using remote image '{data.src}'")
            self._printer.print(f"Using local image '{data.dst}'")
            self._printer.print("Pulling image...")

    def step(self, data: ImageProgressStep) -> None:
        if data.layer_id:
            self._printer.tick()
        else:
            self._printer.print(data.message)

    def complete(self, data: ImageProgressComplete) -> None:
        self._printer.close()
