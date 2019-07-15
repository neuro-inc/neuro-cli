import abc
from dataclasses import dataclass

from yarl import URL


@dataclass
class StorageProgressStart:
    src: URL
    dst: URL
    size: int


@dataclass
class StorageProgressComplete:
    src: URL
    dst: URL
    size: int


@dataclass
class StorageProgressStep:
    src: URL
    dst: URL
    current: int
    size: int


@dataclass
class StorageProgressMkdir:
    src: URL
    dst: URL


@dataclass
class StorageProgressFail:
    src: URL
    dst: URL
    message: str


class AbstractStorageProgress(abc.ABC):
    # design note:
    # dataclasses used instead of direct passing parameters
    # because a dataclass is forward-compatible
    # but adding a new parameter to callback method
    # effectively breaks all existing code

    @abc.abstractmethod
    def start(self, data: StorageProgressStart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def complete(self, data: StorageProgressComplete) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def step(self, data: StorageProgressStep) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def mkdir(self, data: StorageProgressMkdir) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def fail(self, data: StorageProgressFail) -> None:
        pass  # pragma: no cover


class AbstractDockerImageProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, src: str, dst: str) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def progress(self, message: str, layer_id: str) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def close(self) -> None:
        pass  # pragma: no cover
