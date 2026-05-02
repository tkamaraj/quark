import atexit
import os
import pathlib as pl
import re
import select
import signal as sig
import sys
import termios
import tty
import types
import typing as ty

import parser.internals as pint
import utils.consts as uconst
import utils.loggers as ulog

if ty.TYPE_CHECKING:
    import intrpr.cmd_reslvr as icrsr
    import intrpr.internals as iint


class LogicalErr(Exception):
    pass


class KeyboardInterruptWPrevileges(Exception):
    def __init__(self, msg: str, child_pid: int) -> None:
        super().__init__(msg)
        self.child_pid = child_pid


class InvVarTypErr(Exception):
    def __init__(self, var_nm: str, var_typ: type, got_typ: type,
                 *args, **kwargs):
        self.var_nm = var_nm
        self.var_typ = var_typ
        self.got_typ = got_typ


class InvVarNmErr(Exception):
    def __init__(self, var_nm: str, *args, **kwargs):
        self.var_nm = var_nm


class UnkVarErr(Exception):
    def __init__(self, var_nm: str, *args, **kwargs):
        self.var_nm = var_nm


class InvAccess(Exception):
    pass


class CmdData(ty.NamedTuple):
    cmd_nm: str
    args: tuple[str, ...]
    opts: dict[str, str]
    flags: tuple[str, ...]
    cmd_reslvr: "icrsr.CmdReslvr"
    env_vars: "iint.Env"
    ext_cached_cmds: dict[str, "iint.CmdCacheEntry"]
    term_sz: os.terminal_size | None
    is_tty: bool
    stdin: str | None
    exec_fn: ty.Callable[["ieng.Intrpr", str], int | ty.NoReturn]
    operation: str = ""


class CmdSpec(ty.NamedTuple):
    min_args: int
    max_args: int | float
    opts: tuple[str, ...]
    flags: tuple[str, ...]


class HelpObj(ty.NamedTuple):
    usage: str
    summary: str
    details: tuple[str | tuple[str, ...], ...]


class Path:
    def __init__(self, pth: str) -> None:
        self.pth = os.path.expanduser(pth)
        self.abs_pth = os.path.abspath(self.pth)
        self.reslvd_pth = os.path.realpath(self.abs_pth)

    def join_pth(self, pth2: str) -> pl.Path:
        return pl.Path(os.path.join(self.abs_pth, pth2))

    def exists(self) -> bool:
        return os.path.exists(self.reslvd_pth)


class WrapGeneratorToStealReturn:
    def __init__(self, gen: ty.Generator[ty.Any, ty.Any, ty.Any]) -> None:
        self.gen = gen
        self.val = None

    def __iter__(self) -> ty.Generator[ty.Any, ty.Any, ty.Any]:
        self.val = yield from self.gen
        return self.val


class StyleObj:
    """
    Style object to apply formatting to text objects.
    """
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    red_4 = "\x1b[31m"
    green_4 = "\x1b[32m"
    yellow_4 = "\x1b[33m"
    blue_4 = "\x1b[34m"
    magenta_4 = "\x1b[35m"
    cyan_4 = "\x1b[36m"

    green_bg_8 = "\x1b[48;5;22m"
    magenta_bg_8 = "\x1b[48;5;55m"
    white_bg_8 = "\x1b[48;5;248m"
    black_fg_8 = "\x1b[38;5;0m"

    def fmt(self, string: str, apply_fmting: bool, *args: str) -> str:
        return (
            ("".join(args) + string + self.reset) if apply_fmting else string
        )


def ljust(string: str, amt: int) -> str:
    return string.ljust(amt + len(string) - len(rm_ansi("", string)))


def rjust(string: str, amt: int) -> str:
    return string.rjust(amt + len(string) - len(rm_ansi("", string)))


def esc_chrs(s: str, extra: tuple[str]) -> str:
    to_ret = []
    for ch in s:
        if ch in pint.REV_ESC_CHR_MAP:
            to_ret.append(pint.REV_ESC_CHR_MAP[ch])
            continue
        if ch in extra:
            to_ret.append("\\" + ch)
            continue
        to_ret.append(ch)
    return "".join(to_ret)


def set_lgrs(lgrs) -> None:
    global _lgrs
    _lgrs = lgrs


def write(s: str, flush: bool = True) -> None:
    sys.stdout.write(s)
    sys.stdout.flush() if flush else None


def lg_to_fl(lvl: str, txt: str) -> None:
    if lvl == "c":
        _lgrs.fl_lgr.critical(txt)
    elif lvl == "f":
        _lgrs.fl_lgr.fatal(txt)


def fatal(msg: str, ret: int, exc_txt: str | None = None) -> ty.NoReturn:
    _lgrs.lgr_c.fatal(msg)
    _lgrs.fl_lgr.fatal(msg if exc_txt is None else exc_txt)
    sys.exit(ret)


def fatal_Q(msg: str, ret: int, exc_txt: str | None = None) -> ty.NoReturn:
    # To output to STDERR before initialisation of loggers
    if _lgrs is not None:
        _lgrs.lgr_q.fatal(msg)
        _lgrs.fl_lgr.fatal(msg if exc_txt is None else exc_txt)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_RED_4
            + "FQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()
    sys.exit(ret)


def crit(msg: str) -> None:
    _lgrs.lgr_c.critical(msg)
    _lgrs.fl_lgr.critical(msg)


def crit_Q(msg: str) -> None:
    # To output to STDERR before initialisation of loggers
    if _lgrs is not None:
        _lgrs.lgr_q.critical(msg)
        _lgrs.fl_lgr.critical(msg)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_RED_4
            + "CQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()


def err(msg: str) -> None:
    _lgrs.lgr_c.error(msg)
    _lgrs.fl_lgr.error(msg)


def err_Q(msg: str) -> None:
    # To output to STDERR before initialisation of loggers
    if _lgrs is not None:
        _lgrs.lgr_q.error(msg)
        _lgrs.fl_lgr.error(msg)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_RED_4
            + "EQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()


def warn(msg: str) -> None:
    _lgrs.lgr_c.warning(msg)
    _lgrs.fl_lgr.warning(msg)


def warn_Q(msg: str) -> None:
    # To output to STDERR before initialisation of loggers
    if _lgrs is not None:
        _lgrs.lgr_q.warning(msg)
        _lgrs.fl_lgr.warning(msg)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_YELLOW_4
            + "WQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()


def info(msg: str) -> None:
    _lgrs.lgr_c.info(msg)
    _lgrs.fl_lgr.info(msg)


def info_Q(msg: str) -> None:
    # To output to STDERR before initialisation of loggers
    if _lgrs is not None:
        _lgrs.lgr_q.info(msg)
        _lgrs.fl_lgr.info(msg)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_4
            + "IQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()


def debug(msg: str) -> None:
    _lgrs.lgr_c.debug(msg)
    _lgrs.fl_lgr.debug(msg)


def debug_Q(msg: str) -> None:
    if _lgrs is not None:
        _lgrs.lgr_q.debug(msg)
        _lgrs.fl_lgr.debug(msg)
    else:
        sys.stderr.write(
            uconst.ANSI_BOLD_4
            + "DQ:"
            + uconst.ANSI_RESET
            + " "
            + msg
        )
        sys.stderr.flush()


def fmt_d_stmt(src: str, lhs: str, rhs: str | None = None, pad: int = 24) \
        -> str:
    full_str = f"[{src}] {lhs}".ljust(pad)
    if rhs:
        full_str += f" -> {rhs}"
    return full_str


# Source - https://stackoverflow.com/a/46675451
# Posted by netzego, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-01, License - CC BY-SA 3.0
def get_pos() -> tuple[int, int] | None:
    buf = ""
    stdin = sys.stdin.fileno()
    tattr = termios.tcgetattr(stdin)

    try:
        tty.setcbreak(stdin, termios.TCSANOW)
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()
        while True:
            buf += sys.stdin.read(1)
            if buf[-1] == "R":
                break
    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, tattr)

    # Reading the actual values, but what if a keystroke appears while reading
    # from stdin? As dirty work around, getpos() returns if this fails: None
    try:
        matches = re.match(get_pos_regex, buf)
        groups = matches.groups()
    except AttributeError:
        return None

    return (int(groups[0]), int(groups[1]))


class InpHdlr:
    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.old_sett = termios.tcgetattr(self.fd)
        atexit.register(self.reset_sett)

    def set_new_sett(self):
        tty.setraw(self.fd)

    def reset_sett(self) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_sett)

    def kbhit(self, timeout=0):
        r, _, _ = select.select([self.fd], [], [], timeout)
        return bool(r)

    def getch(self) -> str:
        return os.read(self.fd, 1).decode()


def inp(inp_hdlr: InpHdlr, hist: str, tab_spaces: int = 4) -> str:
    init_pos = get_pos()
    while init_pos is None:
        init_pos = get_pos()
    init_ln, init_col = init_pos
    cur_ln, cur_col = init_ln, init_col
    prev_ch = None
    ch = None
    buf = []
    # TODO: Make it include current line being typed in history, i.e. you get
    # last entry in history to be the current line being typed. Tried to
    # implement, but it wouldn't work
    # hist.append("")
    hist_len = len(hist)
    hist_pos = hist_len
    inp_hdlr.set_new_sett()

    while True:
        ins_ch = False
        full_key = inp_hdlr.getch()
        while inp_hdlr.kbhit():
            full_key += inp_hdlr.getch()

        # For tab completion
        # write(mv_cur(cur_ln + 1, 0))
        # write("\x1b[0J")
        # write(mv_cur(cur_ln, cur_col))

        # ^a - move to start of line
        if full_key == "\x01":
            cur_col = init_col

        # ^b or left - move one character back
        elif full_key in ("\x02", "\x1b[D"):
            cur_col -= 1 if cur_col > init_col else 0

        # ^c - interrupt
        elif full_key == "\x03":
            raise KeyboardInterrupt

        # ^d - EOF or kill character under cursor
        elif full_key in ("\x04", "\x1b[3~"):
            # EOF only if ^d
            if not buf and full_key != "\x1b[3~":
                raise EOFError
            # Kill character under cursor
            if cur_col < init_col + len(buf):
                buf.pop(cur_col - init_col)

        # ^e - move to end of line
        elif full_key == "\x05":
            cur_col = init_col + len(buf)

        # ^f or right - move one character forward
        elif full_key in ("\x06", "\x1b[C"):
            cur_col += 1 if cur_col < init_col + len(buf) else 0

        # ^p or up - previous match from history
        elif full_key in ("\x10", "\x1b[A"):
            if hist and hist_pos > 0:
                hist_pos -= 1
                buf = list(hist[hist_pos])
                cur_col = init_col + len(buf)

        # ^n or down - next match from history
        elif full_key in ("\x0e", "\x1b[B"):
            if hist and hist_pos < hist_len - 1:
                hist_pos += 1
                buf = list(hist[hist_pos])
                cur_col = init_col + len(buf)

        # ^u - clear line
        elif full_key == "\x15":
            buf.clear()
            cur_col = init_col

        # ^w - kill word before cursor
        elif full_key == "\x17":
            # Delete whitespace just before cursor before deleting word
            while buf and buf[cur_col - init_col - 1].isspace():
                cur_col -= 1
                buf.pop(cur_col - init_col)
            # Delete the word (i.e. till we hit whitespace again)
            while buf and not buf[cur_col - init_col - 1].isspace():
                cur_col -= 1
                buf.pop(cur_col - init_col)

        elif full_key == "\x0c":
            write("Work in progress")

        # alt+b or ^left - move one word backward
        # No buffer modification. While the start of the buffer is not reached
        # (which happens when current column is same as initial column) and
        # character before the cursor is to be jumped (trailing whitespace or
        # actual word character), then move the cursor one character back
        elif full_key in ("\x1bb", "\x1b[1;5D"):
            # Whitespace before cursor and after previous word
            while cur_col > init_col and buf[cur_col - init_col - 1].isspace():
                cur_col -= 1
            # Actual word
            while (
                cur_col > init_col
                and not buf[cur_col - init_col - 1].isspace()
            ):
                cur_col -= 1

        # alt+d or ^del - kill word forward
        # Current column does not change; current index in the buffer is
        # calculated, and while it's less than length of the buffer (ensure
        # delete range does not go beyond buffer) pop character under cursor
        # (i.e. character at current index)
        elif full_key in ("\x1bd", "\x1b[3;5~"):
            curr_idx = cur_col - init_col
            # Kill whitespace after cursor and before next word
            while curr_idx < len(buf) and buf[cur_col - init_col].isspace():
                buf.pop(cur_col - init_col)
            # Kill actual word forward
            while (
                curr_idx < len(buf)
                and not buf[cur_col - init_col].isspace()
            ):
                buf.pop(cur_col - init_col)

        # alt+f or ^right - move one word forward
        elif full_key in ("\x1bf", "\x1b[1;5C"):
            # Whitespace after cursor and before next word
            while (
                cur_col < init_col + len(buf)
                and buf[cur_col - init_col].isspace()
            ):
                cur_col += 1
            # The actual word
            while (
                cur_col < init_col + len(buf)
                and not buf[cur_col - init_col].isspace()
            ):
                cur_col += 1

        # Backspace (kill char before cursor)
        elif full_key == "\x7f":
            if buf and cur_col > init_col:
                cur_col -= 1
                buf.pop(cur_col - init_col)

        # Tab
        elif full_key == "\t":
            for i in range(tab_spaces):
                buf.insert(cur_col - init_col, " ")
                cur_col += 1
        # Tab (completion)
        # elif full_key == "\t":
        #     mv_cur(cur_ln + 1, 0)
        #     items = os.listdir(".")
        #     write(f"\n{mv_cur_col(0)}".join(items))
        #     mv_cur(cur_ln, cur_col)

        # Return
        elif full_key in ("\r", "\n"):
            write(mv_cur_col(0) + "\n", flush=True)
            break

        # ^z - send SIGSTOP to self
        elif full_key == "\x1a":
            inp_hdlr.reset_sett()
            os.kill(os.getpid(), sig.SIGSTOP)
            cur_pos = get_pos()
            while cur_pos is None:
                cur_pos = get_pos()
            cur_ln, cur_col = cur_pos

        # Ununsed
        elif full_key in (
            "\x00", "\x1c", "\x1d", "\x1e", "\x1f", "\x7f",        # Number row
            "\x11", "\x12", "\x14", "\x19", "\x0f", "\x1c",        # Top row
            "\x13", "\x07", "\x08", "\n", "\x0b",                  # Middle row
            "\x18", "\x16", "\x02", "\x0e", "\r", "\x1f",          # Bottom row
        ):
            pass

        else:
            ins_ch = True

        if ins_ch:
            buf.insert(cur_col - init_col, full_key)
            cur_col += 1
        # cols = os.get_terminal_size().columns
        # for i, sli in enumerate(buf[:: cols - init_cols]):
        #     if i 
        write(mv_cur(cur_ln, init_col) + str_join(buf).expandtabs(4))
        write(uconst.ANSI_ERASE_CUR_TO_EOL)
        write(mv_cur_col(cur_col))

    return str_join(buf)


rm_ansi = re.compile(r"""\x1b\[[;\d]*[A-Za-z]""", re.VERBOSE).sub
_lgrs = None
S = StyleObj()

# For inp()
get_pos_regex = re.compile(r"^\x1b\[(\d*);(\d*)R")
str_join = "".join
mv_cur = lambda ln, col: f"\x1b[{ln};{col}H"
mv_cur_col = lambda col: f"\x1b[{col}G"


def test():
    h = InpHdlr()
    h.set_new_sett()
    k = h.getch()
    while h.kbhit():
        k += h.getch()
    print(repr(k))
