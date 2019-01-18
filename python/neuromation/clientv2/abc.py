import abc


class AbstractProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, file: str, size: int) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def complete(self, file: str) -> None:  # pragma: no cover
        pass

    @abc.abstractmethod
    def progress(self, file: str, current: int) -> None:  # pragma: no cover
        pass
