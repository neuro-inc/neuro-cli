from typing import Dict, Optional

from neuromation.api import AbstractDockerImageProgress, DockerImageOperation
from neuromation.cli.printer import StreamPrinter, TTYPrinter


class DockerImageProgress(AbstractDockerImageProgress):
    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        pass

    @classmethod
    def create(
        cls,
        type: DockerImageOperation,
        input_image: str,
        output_image: str,
        tty: bool,
        quiet: bool,
    ) -> "DockerImageProgress":
        if quiet:
            progress = DockerImageProgress()
        elif tty:
            progress = DetailedDockerImageProgress()
        else:
            progress = StreamDockerImageProgress()

        if type == DockerImageOperation.PUSH:
            progress(f"Using local image '{input_image}'")
            progress(f"Using remote image '{output_image}'")
            progress("Pushing image...")
        elif type == DockerImageOperation.PULL:
            progress(f"Using remote image '{input_image}'")
            progress(f"Using local image '{output_image}'")
            progress("Pulling image...")
        return progress


class DetailedDockerImageProgress(DockerImageProgress):
    def __init__(self) -> None:
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
    def __init__(self) -> None:
        self._printer = StreamPrinter()
        pass

    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        if layer_id:
            self._printer.tick()
        else:
            self._printer.print(message)

    def close(self) -> None:
        super().close()
        self._printer.close()
