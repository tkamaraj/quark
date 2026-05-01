import typing as ty

if ty.TYPE_CHECKING:
    import intrpr.internals as iint

# Colour codes
_ANSI_RESET = "\x1b[0m"
_ANSI_RED = "\x1b[31m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_BLUE = "\x1b[34m"

# PTH = ("@bin",)
ALIASES = {
    "dir": "ls",
    "copy": "cp",
    "wc": "cnt"
}
