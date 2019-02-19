from typing import Optional


def truncate_string(input: Optional[str], max_length: int) -> str:
    if input is None:
        return ""
    if len(input) <= max_length:
        return input
    len_tail, placeholder = 3, "..."
    if max_length < len_tail or max_length < len(placeholder):
        return placeholder
    tail = input[-len_tail:] if max_length > len(placeholder) + len_tail else ""
    index_stop = max_length - len(placeholder) - len(tail)
    return input[:index_stop] + placeholder + tail


def wrap(text: Optional[str]) -> str:
    return "'" + (text or "") + "'"
