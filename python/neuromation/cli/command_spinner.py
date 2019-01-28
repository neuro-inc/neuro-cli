from typing import Any, List

from neuromation.client import AbstractSpinner


class SpinnerBase(AbstractSpinner):
    def start(self, message: str = None) -> None:
        pass

    def complete(self, message: str = None) -> None:
        pass

    def tick(self) -> None:
        pass

    @classmethod
    def create_spinner(
        cls, show_spinner: bool, *args: Any, **kwargs: Any
    ) -> "SpinnerBase":
        if show_spinner:
            return StandardSpinner(*args, **kwargs)
        return SpinnerBase()


class StandardSpinner(SpinnerBase):
    sequence: List[str]
    format_message: str
    step: int = 0

    def __init__(
        self, format_message: str = "{}", sequence: List[str] = ["|", "\\", "-", "/"]
    ) -> "None":
        self.format_message = format_message
        self.sequence = sequence

    def start(self, message: str = None) -> None:
        self.step = 0
        if message:
            print(f"\r{message}", end="")

    def complete(self, message: str = None) -> None:
        if message:
            print(f"\r{message}")
        else:
            print("\r", end="")

    def tick(self) -> None:
        message = self.format_message.format(
            self.sequence[self.step % len(self.sequence)]
        )
        print(f"\r{message}", end="")
        self.step = self.step + 1
