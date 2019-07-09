from typing import Dict, Optional

from neuromation.api import AbstractDockerImageProgress, DockerImageOperation
from neuromation.cli.printer import StreamPrinter, TTYPrinter


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

    def start(self, src: str, dst: str) -> None:
        if self._type == DockerImageOperation.PUSH:
            self(f"Using local image '{src}'")
            self(f"Using remote image '{dst}'")
            self("Pushing image...")
        elif self._type == DockerImageOperation.PULL:
            self(f"Using remote image '{src}'")
            self(f"Using local image '{dst}'")
            self("Pulling image...")


class QuietDockerImageProgress(DockerImageProgress):
    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        pass

    def close(self) -> None:
        pass


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self, type: DockerImageOperation) -> None:
        super().__init__(type)
        self._mapping: Dict[str, int] = {}
        self._printer = TTYPrinter()

    def __call__(self, message: str, layer_id: Optional[str] = None) -> None:
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

    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        if layer_id:
            self._printer.tick()
        else:
            self._printer.print(message)

    def close(self) -> None:
        super().close()
        self._printer.close()
