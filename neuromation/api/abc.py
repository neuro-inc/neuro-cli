import abc
from dataclasses import dataclass

from yarl import URL


# storage


@dataclass(frozen=True)
class StorageProgressStart:
    src: URL
    dst: URL
    size: int


@dataclass(frozen=True)
class StorageProgressComplete:
    src: URL
    dst: URL
    size: int


@dataclass(frozen=True)
class StorageProgressStep:
    src: URL
    dst: URL
    current: int
    size: int


@dataclass(frozen=True)
class StorageProgressEnterDir:
    src: URL
    dst: URL


@dataclass(frozen=True)
class StorageProgressLeaveDir:
    src: URL
    dst: URL


@dataclass(frozen=True)
class StorageProgressFail:
    src: URL
    dst: URL
    message: str


class AbstractFileProgress(abc.ABC):
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


class AbstractRecursiveFileProgress(AbstractFileProgress):
    @abc.abstractmethod
    def enter(self, data: StorageProgressEnterDir) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def leave(self, data: StorageProgressLeaveDir) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def fail(self, data: StorageProgressFail) -> None:
        pass  # pragma: no cover


# image


@dataclass(frozen=True)
class ImageProgressStart:
    src: str
    dst: str


@dataclass(frozen=True)
class ImageProgressStep:
    message: str
    layer_id: str


@dataclass(frozen=True)
class ImageProgressComplete:
    pass  # to be extended later


class AbstractDockerImageProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, data: ImageProgressStart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def step(self, data: ImageProgressStep) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def complete(self, data: ImageProgressComplete) -> None:
        pass  # pragma: no cover
