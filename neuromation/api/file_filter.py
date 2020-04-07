import re
from typing import Any, Callable, List, Tuple, cast


class FileFilter:
    def __init__(self) -> None:
        self.filters: List[Tuple[bool, Callable[[str], Any]]] = []

    def append(self, exclude: bool, pattern: str) -> None:
        if "/" not in pattern.rstrip("/"):
            pattern = "**/" + pattern
        re_pattern = translate(pattern)
        matcher = cast(
            Callable[[str], Any], re.compile(re_pattern, re.DOTALL).fullmatch
        )
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


def translate(pat: str) -> str:
    """Translate a shell PATTERN to a regular expression.
    """

    i = 0
    n = len(pat)
    res = ""
    while i < n:
        c = pat[i]
        i += 1
        if c == "*":
            if (
                (not res or res[-1] == "/")
                and i < n
                and pat[i] == "*"
                and (i + 1 == n or pat[i + 1] == "/")
            ):
                # ** between slashes or ends of the pattern
                if i + 1 == n:
                    res += ".*"
                else:
                    res += "(?:.+/)?"
                i += 2
            else:
                # Any other *
                res += "[^/]*"
        elif c == "?":
            res += "[^/]"
        elif c == "/":
            res += "/"
        elif c == "[":
            j = i
            if j < n and pat[j] == "!":
                j += 1
            if j < n and pat[j] == "]":
                j += 1
            while j < n and pat[j] != "]":
                j += 1
            if j >= n:
                res += "\\["
            else:
                stuff = pat[i:j]
                if "--" not in stuff:
                    stuff = stuff.replace("\\", r"\\")
                else:
                    chunks = []
                    k = i + 2 if pat[i] == "!" else i + 1
                    while True:
                        k = pat.find("-", k, j)
                        if k < 0:
                            break
                        chunks.append(pat[i:k])
                        i = k + 1
                        k = k + 3
                    chunks.append(pat[i:j])
                    # Escape backslashes and hyphens for set difference (--).
                    # Hyphens that create ranges shouldn't be escaped.
                    stuff = "-".join(
                        s.replace("\\", r"\\").replace("-", r"\-") for s in chunks
                    )
                # Escape set operations (&&, ~~ and ||).
                stuff = re.sub(r"([&~|])", r"\\\1", stuff)
                i = j + 1
                if stuff[0] == "!":
                    stuff = "^" + stuff[1:]
                elif stuff[0] in ("^", "["):
                    stuff = "\\" + stuff
                res = "%s[%s](?<!/)" % (res, stuff)
        else:
            res += re.escape(c)
    return res
