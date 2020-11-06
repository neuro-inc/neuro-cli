import abc
from typing import Dict, Iterable

from rich import box
from rich.console import Console, RenderableType
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn
from rich.table import Table

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
from neuromation.cli.printer import StreamPrinter

from .utils import ImageFormatter


class DockerImageProgress(AbstractDockerImageProgress):
    @classmethod
    def create(cls, console: Console, quiet: bool) -> "DockerImageProgress":
        if quiet:
            progress: DockerImageProgress = QuietDockerImageProgress()
        elif console.is_terminal:
            progress = DetailedDockerImageProgress(console)
        else:
            progress = StreamDockerImageProgress(console)
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
    def __init__(self, console: Console) -> None:
        self._mapping: Dict[str, int] = {}
        self._progress = Progress(
            TextColumn("[progress.description]{task.fields[layer]}"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            console=console,
            auto_refresh=False,
        )
        self._progress.start()

    def push(self, data: ImageProgressPush) -> None:
        self._progress.log(f"Pushing image [b]{data.src}[/b] => [b]{data.dst}[/b]")

    def pull(self, data: ImageProgressPull) -> None:
        self._progress.log(f"Pulling image [b]{data.src}[/b] => [b]{data.dst}[/b]")

    def step(self, data: ImageProgressStep) -> None:
        if data.layer_id:
            if data.status in ("Layer already exists", "Download complete"):
                current = 100.0
                total = 100.0
            else:
                current = float(data.current) if data.current is not None else None
                total = float(data.total) if data.total is not None else None
            # self._progress.print(data.layer_id, current, total)
            layer = data.layer_id
            if layer in self._mapping.keys():
                task = self._mapping[layer]
            else:
                task = self._progress.add_task(layer, layer=layer)
                self._mapping[layer] = task

            self._progress.update(
                task,
                description=data.status,
                visible=True,
                completed=current,
                total=total,
                refresh=True,
            )
            for word in ("complete", "pushed", "already"):
                if word in data.status.lower():
                    self._progress.stop_task(task)
            # self._progress.refresh()
        else:
            self._console.log(data.message)

    def save(self, data: ImageProgressSave) -> None:
        self._console.print(f"Saving [b]{data.job}[/b] -> [b]{data.dst}[/b]")

    def commit_started(self, data: ImageCommitStarted) -> None:
        self._console.log(
            f"Creating image [b]{data.target_image}[/b] image from the job container"
        )

    def commit_finished(self, data: ImageCommitFinished) -> None:
        self._console.log("Image created")

    def close(self) -> None:
        self._progress.stop()


class StreamDockerImageProgress(DockerImageProgress):
    def __init__(self, console: Console) -> None:
        self._printer = StreamPrinter()
        self._console = console

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
    def __call__(self, images: Iterable[RemoteImage]) -> RenderableType:
        raise NotImplementedError


class ShortImagesFormatter(BaseImagesFormatter):
    def __call__(self, images: Iterable[RemoteImage]) -> RenderableType:
        table = Table.grid()
        table.add_column("", style="underline")
        for image in images:
            table.add_row(self._format_image(image))
        return table


class LongImagesFormatter(BaseImagesFormatter):
    def __call__(self, images: Iterable[RemoteImage]) -> RenderableType:
        table = Table(box=box.SIMPLE_HEAVY)
        table.add_column("Neuro URL", style="underline")
        table.add_column("Docker URL", style="underline")
        for image in images:
            table.add_row(
                self._format_image(image), image.as_docker_url(with_scheme=True)
            )
        return table
