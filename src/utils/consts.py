import os
import sys
import typing as ty

import parser.internals as pint
if ty.TYPE_CHECKING:
    import intrpr.internals as iint

VER = "0.1"
TAB_SZ = 2

RUN_PTH = os.path.dirname(os.path.abspath(sys.argv[0]))
BIN_PTH = os.path.join(RUN_PTH, "bin")
USR_BIN_PTH = os.path.join(os.path.expanduser("~"), "bin")
SYS_BIN_PTHS = (
    "/usr/bin",
    "/usr/sbin",
    "/usr/local/bin",
    "/usr/local/sbin",
    "/bin",
    "/sbin"
)
CFG_FL = os.path.join(RUN_PTH, "cfg.py")
BUILTIN_PTH = os.path.join(RUN_PTH, "intrpr", "builtin_cmds")
HIST_FL = os.path.join(RUN_PTH, "quark_hist.txt")
LOG_FL = os.path.join(RUN_PTH, "quark.log")

SP_CHRS = pint.LOGI_OPS + pint.DATA_OPS + pint.CMD_SEPRS + pint.GLOB_CHS

ANSI_RESET = "\x1b[0m"
ANSI_BOLD = "\x1b[1m"
ANSI_BLINK_4 = "\x1b[5m"
ANSI_BLUE_4 = "\x1b[94m"
ANSI_CLS_4 = "\x1b[H\x1b[J"
ANSI_CYAN_4 = "\x1b[96m"
ANSI_GREEN_4 = "\x1b[92m"
ANSI_HEADER_4 = "\x1b[95m"
ANSI_RED_4 = "\x1b[91m"
ANSI_UNDERLINE_4 = "\x1b[4m"
ANSI_YELLOW_4 = "\x1b[93m"
ANSI_BOLD_RED_4 = ANSI_BOLD + ANSI_RED_4
ANSI_BOLD_YELLOW_4 = ANSI_BOLD + ANSI_YELLOW_4
ANSI_ERASE_CUR_TO_EOL = "\x1b[0K"
ANSI_ERASE_FULL_LN = "\x1b[2K"


# For default prompt value
usr = f"{ANSI_BLUE_4}!u{ANSI_RESET}"
host = f"{ANSI_YELLOW_4}!h{ANSI_RESET}"
cwd = f"{ANSI_GREEN_4}!P{ANSI_RESET}"


class Defaults:
    ALIASES: dict[str, str]

    PTH = (USR_BIN_PTH, *SYS_BIN_PTHS, BIN_PTH)
    ALIASES = {}
    LN_MODE = "emacs"

    # PROMPT = f"┌ !? {ANSI_BLUE_4}!u{ANSI_RESET}@{ANSI_YELLOW_4}!h{ANSI_RESET} {ANSI_GREEN_4}!P{ANSI_RESET}\n└─❯ "
    @staticmethod
    def PROMPT(intrpr_vars: "iint.IntrprTbl") -> str:
        if intrpr_vars["_LAST_RET_"] != 0:
            err = f"{ANSI_RED_4}•!?{ANSI_RESET}"
        else:
            err = f"{ANSI_GREEN_4}•{ANSI_RESET}"
        return f"┌ {err} {usr}@{host} {cwd}\n└─❯ "


class ValidVals:
    LN_MODE = {"emacs", "vi", "raw"}
