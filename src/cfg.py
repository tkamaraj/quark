import typing as ty

if ty.TYPE_CHECKING:
    import intrpr.internals as iint

# Colour codes
_ANSI_RESET = "\x1b[0m"
_ANSI_RED = "\x1b[31m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_BLUE = "\x1b[34m"

PTH = ("@bin",)
ALIASES = {
    "dir": "ls",
    "copy": "cp",
    "wc": "cnt"
}

usr = f"{_ANSI_BLUE}!u{_ANSI_RESET}"
host = f"{_ANSI_YELLOW}!h{_ANSI_RESET}"
cwd = f"{_ANSI_GREEN}!P{_ANSI_RESET}"


def PROMPT(env_vars: "iint.Env") -> str:
    if env_vars.get("_LAST_RET_") != 0:
        err = f"{_ANSI_RED}•!?{_ANSI_RESET}"
    else:
        err = f"{_ANSI_GREEN}•{_ANSI_RESET}"

    return f"┌ {err} {usr}@{host} {cwd}\n└─❯ "
