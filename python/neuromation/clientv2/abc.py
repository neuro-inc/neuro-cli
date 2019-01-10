import abc


class AbstractProgress(abc.ABC):
    @abc.abstractmethod
    def start(self, file: str, size: int) -> None:
        pass

    @abc.abstractmethod
    def complete(self, file: str) -> None:
        pass

    @abc.abstractmethod
    def progress(self, file: str, current: int) -> None:
        pass
