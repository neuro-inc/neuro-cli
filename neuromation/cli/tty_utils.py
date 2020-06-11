import sys
from ctypes import c_ulong


# Input/Output standard device numbers. Note that these are not handle objects.
# It's the `windll.kernel32.GetStdHandle` system call that turns them into a
# real handle object.
STD_INPUT_HANDLE = c_ulong(-10)
STD_OUTPUT_HANDLE = c_ulong(-11)
STD_ERROR_HANDLE = c_ulong(-12)

# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def enable_ansi() -> None:
    if not sys.stdout.isatty():
        return
    if sys.platform == "win32":
        from ctypes import windll
        from ctypes.wintypes import DWORD, HANDLE

        hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))

        # Enable processing of vt100 sequences.
        result = windll.kernel32.SetConsoleMode(
            hconsole,
            DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING),
        )

        if result != 1:
            raise RuntimeError("Windows 10 is required.")
    else:
        return
