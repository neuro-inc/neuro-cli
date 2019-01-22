from neuromation.clientv2 import AbstractSpinner
from typing import List

class SpinnerBase(AbstractSpinner):
    def start(self, message: str = None):
        pass

    def complete(self, message: str = None):
        pass

    def tick(self):
        pass

    @classmethod
    def create_spinner(cls, show_spinner: bool, *args, **kwargs) -> "SpinnerBase":
        if show_spinner:
            return StandardSpinner(*args, **kwargs)
        return SpinnerBase()


class StandardSpinner(SpinnerBase):
    sequence: List[str]
    format_message: str
    step: int = 0

    def __init__(self, format_message: str = '{}', sequence: List[str] = ['|', '\\', '-', '/']):
        self.format_message = format_message
        self.sequence = sequence

    def start(self,  message: str = None):
        self.step = 0
        if message:
            print(f'\r{message}', end='')

    def complete(self, message: str = None):
        if message:
            print(f'\r{message}')
        else:
            print('\r', end='')

    def tick(self):
        message = self.format_message.format(self.sequence[self.step % len(self.sequence)])
        print(f'\r{message}', end='')
        self.step = self.step + 1
