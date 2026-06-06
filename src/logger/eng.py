import io
import enum
import os
import sys
import typing as ty

import utils.consts as uconst
import utils.gen as ugen


def set_log_lvl(lvl: int) -> None | ty.NoReturn:
    if lvl not in LogLvls:
        raise ValueError(f"Invalid log level: {lvl}")
    global LOG_LVL
    LOG_LVL = lvl
    return None


class LogLvls(enum.IntEnum):
    DEBUG = 1
    INFO = enum.auto()
    WARN = enum.auto()
    ERR = enum.auto()
    CRIT = enum.auto()
    FATAL = enum.auto()


class LogData(ty.NamedTuple):
    nm: str
    msg: str
    lvl: int


class Lgr:
    def __init__(
        self,
        nm: str,
        src: str,
        lvl: int,
        stream: io.TextIOBase
    ) -> None:
        self.nm = nm
        self.src = src
        self.lvl = lvl
        self.stream = stream
        self.fl_num = self.stream.fileno()

    def _log(self, msg: str, lvl: int, fmting: str | None = None) -> None:
        if lvl < LOG_LVL:
            return
        os.write(
            self.fl_num,
            (
                (fmting if fmting is not None else "")
                + ERR_HEADER_MAP[lvl]
                + self.src
                + (ugen.S.reset if fmting is not None else "")
                + f" {msg}\n"
            ).encode()
        )

    def debug(self, msg: str) -> None:
        self._log(msg, LogLvls.DEBUG, fmting=ugen.S.bold)

    def info(self, msg: str) -> None:
        self._log(msg, LogLvls.INFO, fmting=ugen.S.bold)

    def warn(self, msg: str) -> None:
        self._log(msg, LogLvls.WARN, fmting=ugen.S.bold + ugen.S.yellow_4)

    def err(self, msg: str) -> None:
        self._log(msg, LogLvls.ERR, fmting=ugen.S.bold + ugen.S.red_4)

    def crit(self, msg: str) -> None:
        self._log(msg, LogLvls.CRIT, fmting=ugen.S.bold + ugen.S.red_4)

    def fatal(self, msg: str) -> None:
        self._log(msg, LogLvls.FATAL, fmting=ugen.S.bold + ugen.S.red_4)


class LgrVessel(ty.NamedTuple):
    lgr_c: Lgr
    lgr_q: Lgr
    fl_lgr: Lgr


ERR_HEADER_MAP: dict[int, str]

# Default log level is ERR
LOG_LVL = LogLvls.ERR
ERR_HEADER_MAP = {
    LogLvls.DEBUG: "D",
    LogLvls.INFO : "I",
    LogLvls.WARN : "W",
    LogLvls.ERR  : "E",
    LogLvls.CRIT : "C",
    LogLvls.FATAL: "F"
}
