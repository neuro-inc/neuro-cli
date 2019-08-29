import re


def parse_memory(memory: str) -> int:
    """Parse string expression i.e. 16M, 16MB, etc
    M = 1024 * 1024, MB = 1000 * 1000

    returns value in bytes"""

    # Mega, Giga, Tera, etc
    prefixes = "MGTPEZY"
    value_error = ValueError(f"Unable parse value: {memory}")

    if not memory:
        raise value_error

    pattern = r"^(?P<value>\d+)(?P<units>(kB|K)|((?P<prefix>[{prefixes}])(?P<unit>B?)))$".format(  # NOQA
        prefixes=prefixes
    )
    regex = re.compile(pattern)
    match = regex.fullmatch(memory)

    if not match:
        raise value_error

    groups = match.groupdict()

    value = int(groups["value"])
    unit = groups["unit"]
    prefix = groups["prefix"]
    units = groups["units"]

    if units == "kB":
        return value * 1000

    if units == "K":
        return value * 1024

    # Our prefix string starts with Mega
    # so for index 0 the power should be 2
    power = 2 + prefixes.index(prefix)
    multiple = 1000 if unit else 1024

    return value * multiple ** power


def to_megabytes(value: str) -> int:
    return int(parse_memory(value) / (1024 ** 2))
