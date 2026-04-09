import os
import typing as ty

VER = "0.1"
TAB_SZ = 2

RUN_PTH = os.path.dirname(os.path.dirname(__file__))
BIN_PTH = os.path.join(RUN_PTH, "bin")
CFG_FL = os.path.join(RUN_PTH, "cfg.py")
BUILTIN_PTH = os.path.join(RUN_PTH, "intrpr", "builtin_cmds")
HIST_FL = os.path.join(RUN_PTH, "quark_hist.txt")

SP_CHRS = ("|", ">", "?", ";")

ANSI_RESET = "\x1b[0m"
ANSI_BOLD_4 = "\x1b[1m"
ANSI_BLINK_4 = "\x1b[5m"
ANSI_BLUE_4 = "\x1b[94m"
ANSI_CLS_4 = "\x1b[H\x1b[J"
ANSI_CYAN_4 = "\x1b[96m"
ANSI_GREEN_4 = "\x1b[92m"
ANSI_HEADER_4 = "\x1b[95m"
ANSI_RED_4 = "\x1b[91m"
ANSI_UNDERLINE_4 = "\x1b[4m"
ANSI_YELLOW_4 = "\x1b[93m"
ANSI_BOLD_RED_4 = ANSI_BOLD_4 + ANSI_RED_4
ANSI_BOLD_YELLOW_4 = ANSI_BOLD_4 + ANSI_YELLOW_4
ANSI_ERASE_CUR_TO_EOL = "\x1b[0K"
ANSI_ERASE_FULL_LN = "\x1b[2K"


class Defaults:
    PROMPT = f"┌ !? {ANSI_BLUE_4}!u{ANSI_RESET}@{ANSI_YELLOW_4}!h{ANSI_RESET} {ANSI_GREEN_4}!P{ANSI_RESET}\n└─❯ "
    PTH = (BIN_PTH,)
