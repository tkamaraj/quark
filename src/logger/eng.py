import enum
import typing as ty

ERR_HEADER_MAP = {
    DEBUG: "D",
    INFO: "I",
    WARN: "W",
    ERR: "E",
    CRIT: "C",
    FATAL: "F",
}


class LgLvls(enum.IntEnum):
    DEBUG = 1
    INFO = enum.auto()
    WARN = enum.auto()
    ERR = enum.auto()
    CRIT = enum.auto()
    FATAL = enum.auto()


class Lgr:
    def __init__(
        self,
        nm: str,
        fmt_str: str,
        lvl: int = LgLvls.ERR,
        stream: io.TextIOBase = sys.stderr
    ) -> None:
        self.nm = nm
        self.fmt_str = fmt_str
        self.stream = stream
        self.lvl = lvl

    def err(self, msg: str) -> None:
        if LOG_LVL < self.lvl:
            return
        self.stream.write(msg)


# Default log level is ERR
LOG_LVL = LgLvls.ERR
