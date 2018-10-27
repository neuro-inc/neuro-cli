

class ProgressBase:  # pragma: no cover
    def start(self, file: str, size: int):
        pass

    def complete(self, file: str):
        pass

    def progress(self, file: str, current: int):
        pass


class StandardPrintPercentOnly(ProgressBase):

    def __init__(self):
        self._file = None
        self._file_size = None

    def start(self, file: str, size: int):
        self._file = file
        self._file_size = size
        print(f"Starting file {file}.")

    def complete(self, file: str):
        self._file = file
        print(f"\rFile {file} upload complete.")

    def progress(self, file: str, current: int):
        self._file = file
        progress = (100 * current) / self._file_size
        print(f"\r{self._file}: {progress:.2f}%.", end="")
