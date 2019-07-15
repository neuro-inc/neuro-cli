import abc

from yarl import URL


class AbstractStorageProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, src: URL, dst: URL, size: int) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def complete(self, src: URL, dst: URL, size: int) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def progress(self, src: URL, dst: URL, current: int, size: int) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def mkdir(self, src: URL, dst: URL) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def fail(self, src: URL, dst: URL, message: str) -> None:
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
