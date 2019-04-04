from typing import Dict, Optional

from neuromation.cli.command_reporter import MultilineReporter, StreamReporter
from neuromation.client import AbstractImageProgress, ImageOperation


class ImageProgress(AbstractImageProgress):
    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        pass

    @classmethod
    def create(
        cls,
        type: ImageOperation,
        input_image: str,
        output_image: str,
        tty: bool,
        quiet: bool,
    ) -> "ImageProgress":
        if quiet:
            progress = ImageProgress()
        elif tty:
            progress = DetailedImageProgress()
        else:
            progress = StreamImageProgress()

        if type == ImageOperation.PUSH:
            progress(f"Using local image '{input_image}'")
            progress(f"Using remote image '{output_image}'")
            progress("Pushing image...")
        elif type == ImageOperation.PULL:
            progress(f"Using remote image '{input_image}'")
            progress(f"Using local image '{output_image}'")
            progress("Pulling image...")
        return progress


class DetailedImageProgress(ImageProgress):
    def __init__(self) -> None:
        self._mapping: Dict[str, int] = {}
        self._reporter = MultilineReporter(print=True)

    def __call__(self, message: str, layer_id: Optional[str] = None) -> None:
        if layer_id:
            if layer_id in self._mapping.keys():
                lineno = self._mapping[layer_id]
                self._reporter.report(message, lineno)
            else:
                self._reporter.report(message)
                self._mapping[layer_id] = self._reporter.total_lines
        else:
            self._reporter.report(message)

    def close(self) -> None:
        super().close()
        self._reporter.close()


class StreamImageProgress(ImageProgress):
    def __init__(self) -> None:
        self._reporter = StreamReporter(print=True)
        pass

    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        if layer_id:
            self._reporter.tick()
        else:
            self._reporter.report(message)

    def close(self) -> None:
        super().close()
        self._reporter.close()
