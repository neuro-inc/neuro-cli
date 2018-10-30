from typing import Any, Callable, Iterator, Tuple


NAMES = ["grey", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
COLOR_FUNCS = {}


def get_pairs() -> Iterator[Tuple[str, str]]:
    for i, name in enumerate(NAMES):
        yield (name, str(30 + i))
        yield ("intense_" + name, str(30 + i) + ";1")


def ansi(code: Any) -> str:
    return "\033[{0}m".format(code)


def ansi_color(code: str, s: str) -> str:
    return "{0}{1}{2}".format(ansi(code), s, ansi(0))


def make_color_fn(code: str) -> Callable[[str], str]:
    return lambda s: ansi_color(code, s)


for (name, code) in get_pairs():
    globals()[name] = make_color_fn(code)
    COLOR_FUNCS[name] = make_color_fn(code)


def rainbow() -> Iterator[str]:
    cs = [
        "cyan",
        "yellow",
        "green",
        "magenta",
        "red",
        "blue",
        "intense_cyan",
        "intense_yellow",
        "intense_green",
        "intense_magenta",
        "intense_red",
        "intense_blue",
    ]

    for c in cs:
        yield globals()[c]
