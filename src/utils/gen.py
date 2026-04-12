import os
import pathlib as pl
import re
import sys
import termios
import tty
import types
import typing as ty

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
    term_sz: os.terminal_size
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


def set_lgrs(lgrs) -> None:
    global _lgrs
    _lgrs = lgrs


def write(s: str, flush: bool = True) -> None:
    sys.stdout.write(s)
    sys.stdout.flush() if flush else None


def fatal(msg: str, ret: int, exc_txt: str | None = None) -> ty.NoReturn:
    """
    Reports a fatal error.

    :param msg: The message
    :type msg: str

    :param ret: Return code for the calling program
    :type ret: int

    :returns: Error code
    :rtype: int
    """
    _lgrs.lgr_c.fatal(msg)
    _lgrs.fl_lgr.fatal(msg if exc_txt is None else exc_txt)
    sys.exit(ret)


def fatal_Q(msg: str, ret: int, exc_txt: str | None = None) -> ty.NoReturn:
    """
    Reports a fatal interpreter error.

    :param msg: The message
    :type msg: str

    :param ret: Return code for the calling program
    :type ret: int

    :returns: Error code
    :rtype: int
    """
    _lgrs.lgr_q.fatal(msg)
    _lgrs.fl_lgr.fatal(msg if exc_txt is None else exc_txt)
    sys.exit(ret)


def crit(msg: str) -> None:
    """
    Reports a critical error.

    :param msg: The message
    :type msg: str

    :param ret: The return code to pass on
    :type ret: int
    """
    _lgrs.lgr_c.critical(msg)
    _lgrs.fl_lgr.critical(msg)


def crit_Q(msg: str) -> None:
    """
    Reports a critical interpreter error.

    :param msg: The message
    :type msg: str

    :param ret: The return code to pass on
    :type ret: int
    :rtype: int
    """
    _lgrs.lgr_q.critical(msg)
    _lgrs.fl_lgr.critical(msg)


def err(msg: str) -> None:
    """
    Reports an error.

    :param msg: The message
    :type msg: str

    :param ret: The return code to pass on
    :type ret: int
    """
    _lgrs.lgr_c.error(msg)
    _lgrs.fl_lgr.error(msg)


def err_Q(msg: str) -> None:
    """
    Reports an interpreter error.

    :param msg: The message
    :type msg: str

    :param ret: The return code to pass on
    :type ret: int
    """
    # To output to STDERR before the initialisation of loggers
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
    """
    Displays a message.

    :param msg: The message
    :type msg: str
    """
    _lgrs.lgr_c.info(msg)
    _lgrs.fl_lgr.info(msg)


def info_Q(msg: str) -> None:
    """
    Displays an interpreter message.

    :param msg: The message
    :type msg: str
    """
    _lgrs.lgr_q.info(msg)
    _lgrs.fl_lgr.info(msg)


def debug(msg: str) -> None:
    """
    Displays a debug message.

    :param msg: The message
    :type msg: str
    """
    _lgrs.lgr_c.debug(msg)
    _lgrs.fl_lgr.debug(msg)


def debug_Q(msg: str) -> None:
    """
    Displays an interpreter debug message.

    :param msg: The message
    :type msg: str
    """
    _lgrs.lgr_q.debug(msg)
    _lgrs.fl_lgr.debug(msg)


def fmt_d_stmt(src: str, lhs: str, rhs: str | None = None, pad: int = 24) \
        -> str:
    full_str = f"[{src}] {lhs}".ljust(pad)
    if rhs:
        full_str += f"-> {rhs}"
    return full_str


def transpose(arr: ty.Iterable) -> ty.Iterable:
    pass


def getch() -> str:
    fd = sys.stdin.fileno()
    old_setts = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_setts)
    return ch


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


# TODO: Really need kbhit()... research more on how to implement it
def inp(hist: str) -> str:
    init_pos = get_pos()
    if init_pos is None:
        err_Q("get_pos() failed; try again")
        return ""
    init_ln, init_col = init_pos
    cur_ln, cur_col = init_ln, init_col
    prev_ch = None
    ch = None
    buf = []
    # TODO: Make it include the current line being typed in the history,
    # meaning, you get the last entry in the history to be the current line
    # being typed. I tried to implement it, but it wouldn't work
    # hist.append("")
    hist_len = len(hist)
    hist_pos = hist_len
    f = open(os.path.join(uconst.RUN_PTH, "quark.txt"), "w")

    while True:
        ins_ch = True
        ch = getch()

        # ^a - move to start of line
        if ch == "\x01":
            ins_ch = False
            cur_col = init_col

        # ^b - move one character back
        elif ch == "\x02":
            ins_ch = False
            cur_col -= 1 if cur_col > init_col else 0

        # ^c - interrupt
        elif ch == "\x03":
            raise KeyboardInterrupt

        # ^d - EOF or kill character under cursor
        elif ch == "\x04":
            ins_ch = False
            # EOF
            if not buf:
                raise EOFError
            # Kill character under cursor
            if cur_col < init_col + len(buf):
                buf.pop(cur_col - init_col)

        # ^e - move to end of line
        elif ch == "\x05":
            ins_ch = False
            cur_col = init_col + len(buf)

        # ^f - move one character forward
        elif ch == "\x06":
            ins_ch = False
            cur_col += 1 if cur_col < init_col + len(buf) else 0

        # ^p - previous match from history
        elif ch == "\x10":
            ins_ch = False
            if hist and hist_pos > 0:
                hist_pos -= 1
                buf = list(hist[hist_pos])
                cur_col = init_col + len(buf)

        # ^n - next match from history
        elif ch == "\x0e":
            ins_ch = False
            if hist and hist_pos < hist_len - 1:
                hist_pos += 1
                buf = list(hist[hist_pos])
                cur_col = init_col + len(buf)

        # ^u - clear line
        elif ch == "\x15":
            ins_ch = False
            buf.clear()
            cur_col = init_col

        # ^w - kill word before cursor
        elif ch == "\x17":
            ins_ch = False
            # Delete whitespace just before cursor before deleting word
            while buf and buf[cur_col - init_col - 1].isspace():
                cur_col -= 1
                buf.pop(cur_col - init_col)
            # Delete the word (i.e. till we hit whitespace again)
            while buf and not buf[cur_col - init_col - 1].isspace():
                cur_col -= 1
                buf.pop(cur_col - init_col)

        elif ch == "\x0c":
            ins_ch = False
            write("Work in progress")

        elif ch == "\x1b":
            # This is one of the ugliest pieces of code I've written in this
            # project
            ins_ch = False
            getch_chrs = []
            i = 0

            while True:
                tmp_ch = getch()
                getch_chrs.append(tmp_ch)
                i += 1

                # 1st getch() after "\x1b"
                if i == 1:
                    # alt+b - move one word backward
                    if tmp_ch == "b":
                        # Whitespace before cursor and after previous word
                        while (
                                cur_col > init_col
                                and buf[cur_col - init_col - 1].isspace()
                        ):
                            cur_col -= 1
                        # The actual word
                        while (
                                cur_col > init_col
                                and not buf[cur_col - init_col - 1].isspace()
                        ):
                            cur_col -= 1

                    # alt+f - move one word forward
                    elif tmp_ch == "f":
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

                    # For arrow and del keys, as well as ^[ and ^], I think.
                    # Must check. TODO: CHECK!
                    elif tmp_ch in ("[", "]"):
                        continue

                    # Continue if no operation matches, because the next
                    # getch() may yield known operations
                    else:
                        continue

                    # Breaks if some operation listed in the if-statements
                    # above is done, i.e. alt+f or alt+b, etc.
                    break

                # 2nd getch() after "\x1b"
                elif i == 2:
                    # del - delete under cursor
                    if tmp_ch == "3":
                        getch()
                        if buf:
                            cur_col -= 1
                            buf.pop(cur_col - init_col + 1)
                    # up - up arrow
                    elif tmp_ch == "A":
                        pass
                    # down - down arrow
                    elif tmp_ch == "B":
                        pass
                    # right - right arrow
                    elif tmp_ch == "C":
                        cur_col += 1 if cur_col < len(buf) + init_col else 0
                    # left - left arrow
                    elif tmp_ch == "D":
                        cur_col -= 1 if cur_col > init_col else 0
                    else:
                        continue
                    break

                else:
                    crit_Q(
                        f"Unknown 1st getch() char for \"\\x1b\": {repr(tmp_ch)}"
                    )
                    break

        # Backspace (kill char before cursor)
        elif ch == "\x7f":
            ins_ch = False
            if buf and cur_col > init_col:
                cur_col -= 1
                buf.pop(cur_col - init_col)

        # Return
        elif ch == "\r":
            write("\n")
            break

        # Ununsed
        elif ch in (
            "\x00", "\x1c", "\x1d", "\x1e", "\x1f", "\x7f",        # Number row
            "\x11", "\x12", "\x14", "\x19", "\x0f", "\x1c",        # Top row
            "\x13", "\x07", "\x08", "\n", "\x0b",                  # Middle row
            "\x1a", "\x18", "\x16", "\x02", "\x0e", "\r", "\x1f",  # Bottom row
        ):
            ins_ch = False

        if ins_ch:
            buf.insert(cur_col - init_col, ch)
            cur_col += 1
        write(mv_cur(cur_ln, init_col) + str_join(buf))
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
