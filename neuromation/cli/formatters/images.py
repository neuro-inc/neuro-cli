from enum import Enum
from typing import Dict

from neuromation.api import AbstractDockerImageProgress
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
    def start(self, src: str, dst: str) -> None:
        pass

    def progress(self, message: str, layer_id: str) -> None:
        pass

    def close(self) -> None:
        pass


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self, type: DockerImageOperation) -> None:
        super().__init__(type)
        self._mapping: Dict[str, int] = {}
        self._printer = TTYPrinter()

    def start(self, src: str, dst: str) -> None:
        if self._type == DockerImageOperation.PUSH:
            self._printer.print(f"Using local image '{src}'")
            self._printer.print(f"Using remote image '{dst}'")
            self._printer.print("Pushing image...")
        elif self._type == DockerImageOperation.PULL:
            self._printer.print(f"Using remote image '{src}'")
            self._printer.print(f"Using local image '{dst}'")
            self._printer.print("Pulling image...")

    def progress(self, message: str, layer_id: str) -> None:
        if layer_id:
            if layer_id in self._mapping.keys():
                lineno = self._mapping[layer_id]
                self._printer.print(message, lineno)
            else:
                self._printer.print(message)
                self._mapping[layer_id] = self._printer.total_lines
        else:
            self._printer.print(message)

    def close(self) -> None:
        super().close()
        self._printer.close()


class StreamDockerImageProgress(DockerImageProgress):
    def __init__(self, type: DockerImageOperation) -> None:
        super().__init__(type)
        self._printer = StreamPrinter()

    def start(self, src: str, dst: str) -> None:
        if self._type == DockerImageOperation.PUSH:
            self._printer.print(f"Using local image '{src}'")
            self._printer.print(f"Using remote image '{dst}'")
            self._printer.print("Pushing image...")
        elif self._type == DockerImageOperation.PULL:
            self._printer.print(f"Using remote image '{src}'")
            self._printer.print(f"Using local image '{dst}'")
            self._printer.print("Pulling image...")

    def progress(self, message: str, layer_id: str) -> None:
        if layer_id:
            self._printer.tick()
        else:
            self._printer.print(message)

    def close(self) -> None:
        super().close()
        self._printer.close()
