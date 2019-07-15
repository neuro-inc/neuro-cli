import abc

from yarl import URL


class AbstractStorageProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, src: URL, dst: URL, size: int) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def complete(self, src: URL, dst: URL) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def progress(self, src: URL, dst: URL, current: int) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def mkdir(self, src: URL, dst: URL) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def fail(self, src: URL, dst: URL, message: str) -> None:  # pragma: no cover
        pass


class AbstractDockerImageProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, src: str, dst: str) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def progress(self, message: str, layer_id: str) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def close(self) -> None:  # pragma: no cover
        pass
