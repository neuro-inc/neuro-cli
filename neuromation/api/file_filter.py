import fnmatch
import re
from typing import Any, Callable, List, Tuple, cast


class FileFilter:
    def __init__(self) -> None:
        self.filters: List[Tuple[bool, Callable[[str], Any]]] = []

    def append(self, exclude: bool, pattern: str) -> None:
        re_pattern = fnmatch.translate(pattern)
        matcher = cast(Callable[[str], Any], re.compile(re_pattern).match)
        self.filters.append((exclude, matcher))

    def exclude(self, pattern: str) -> None:
        self.append(True, pattern)

    def include(self, pattern: str) -> None:
        self.append(False, pattern)

    async def match(self, path: str) -> bool:
        result = True
        for exclude, matcher in self.filters:
            if result == exclude and matcher(path):
                result = not result
        return result
