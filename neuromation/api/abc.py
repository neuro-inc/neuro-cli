import abc
from typing import Optional


class AbstractProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, src: str, dst: str, size: int) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def complete(self, src: str, dst: str) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def progress(self, src: str, dst: str, current: int) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def mkdir(self, src: str, dst: str) -> None:  # pragma: no cover
        pass


class AbstractDockerImageProgress(abc.ABC):
    @abc.abstractmethod
    def __call__(self, message: str, layer_id: Optional["str"] = None) -> None:
        pass

    def close(self) -> None:
        pass
