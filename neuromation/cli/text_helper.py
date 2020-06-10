import re
from difflib import SequenceMatcher
from textwrap import fill, wrap
from typing import Iterator, List, Sequence

import click
from wcwidth import wcswidth


class StyledTextHelper:
    """ Utilities to perform string operations on terminal styled text with better
    unicode support.

    NOTE: The helper does not recognise controll sequences other than SGR
        (Select Graphic Rendition) ones.
    """

    style_re = re.compile(r"(\033\[(?:\d|;)*m)")
    ansi_reset_all = "\033[0m"
    whitespace = "\t\n\x0b\x0c\r "

    @classmethod
    def is_styled(cls, text: str) -> bool:
        return "\033" in text

    # As we often do operations on headers or similar static text it makes sense to
    # cache
    @classmethod
    def unstyle(cls, text: str) -> str:
        return click.unstyle(text)

    @classmethod
    def width(cls, text: str) -> int:
        if cls.is_styled(text):
            return wcswidth(cls.unstyle(text))
        else:
            return wcswidth(text)

    @classmethod
    def ljust(cls, text: str, width: int) -> str:
        if cls.is_styled(text):
            return text.ljust(width + len(text) - len(cls.unstyle(text)))
        else:
            return text.ljust(width)

    @classmethod
    def rjust(cls, text: str, width: int) -> str:
        if cls.is_styled(text):
            return text.rjust(width + len(text) - len(cls.unstyle(text)))
        else:
            return text.rjust(width)

    @classmethod
    def center(cls, text: str, width: int) -> str:
        if cls.is_styled(text):
            return text.center(width + len(text) - len(cls.unstyle(text)))
        else:
            return text.center(width)

    @classmethod
    def trim(cls, text: str, width: int) -> str:
        if not cls.is_styled(text):
            return text[:width]

        result = []
        has_unclosed = False
        remaining = width
        for token in cls.style_re.split(text):
            if cls.style_re.match(token):
                result.append(token)
                # We will need to add a reset at the end if there are any non-closed
                # sequences
                has_unclosed = token != cls.ansi_reset_all
            else:
                if len(token) >= remaining:
                    result.append(token[:remaining])
                    break
                remaining -= len(token)
                result.append(token)

        if has_unclosed:
            result.append(cls.ansi_reset_all)

        return "".join(result)

    @classmethod
    def wrap(cls, text: str, width: int) -> Sequence[str]:
        if cls.is_styled(text):
            # Fast return if we don't need to wrap the text
            if cls.width(text) <= width:
                return [text]

            wrapped = fill(cls.unstyle(text), width)
            return list(cls._reapply_styles(text, wrapped))
        else:
            return wrap(text, width)

    @classmethod
    def _reapply_styles(cls, text: str, wrapped: str) -> Iterator[str]:
        """ Iterate over wrapped text and original one and reapply styles from
        the original to wrapped
        """
        sm = SequenceMatcher(None, text, wrapped)

        result: List[str] = []

        for op, ti, tj, wi, wj in sm.get_opcodes():
            if op == "equal" or op == "insert":
                # For those 2 cases we just take the text wrap() generated for us
                result.append(wrapped[wi:wj])
            if op == "delete" or op == "replace":
                # In those cases we either replaced some whitespace's or need to apply
                # styles from original.

                # The most complicated situation would be if for some reason we had
                # several whitespaces in the styled case that were not replaced by wrap.
                # In this case we have to assume that the positioning of those style
                # codes matter (ex. we want to have 1 space before and after a word
                # underlined). Ex:
                #
                #   Plase select exactly \033[4m one \033[0m word
                #
                ws_buf = wrapped[wi:wj]
                for token in cls.style_re.split(text[ti:tj]):
                    if cls.style_re.match(token):
                        result.append(token)
                    else:
                        # We take the same amount of whitespace from result to preserve
                        # style opcode position
                        ws_len = len(token)
                        # NOTE: ws_buf can be empty at any point
                        result.append(ws_buf[:ws_len])
                        ws_buf = ws_buf[ws_len:]

        # Fix style sequencing on breaklines
        ansi_stack: List[str] = []
        ansi_reset_all = cls.ansi_reset_all
        for line in "".join(result).split("\n"):
            # Strip any reset styling at beginning. Ex: "\033[4m\033[0m word"
            prefix, _, remainder = line.partition(ansi_reset_all)
            if not cls.unstyle(prefix):
                line = remainder
                # We also assume we broke all sequnces from previous lines
                ansi_stack = []

            # Reopen any sequences that were opened before breakline
            if ansi_stack:
                line = "".join(ansi_stack) + line

            # Find sequnces not closed at the end of this line
            ansi_stack = []
            for token in cls.style_re.findall(line):
                if token == ansi_reset_all:
                    ansi_stack = []
                else:
                    # XXX: Add excluding op-codes handling too. Like bold (1) and
                    #      normal (22)
                    ansi_stack.append(token)

            # Break sequnces if we have any opened
            if ansi_stack:
                line += ansi_reset_all

            yield line
        return
