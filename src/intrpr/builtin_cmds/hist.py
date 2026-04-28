import pathlib as pl
import typing as ty

import utils.consts as uconst
import utils.gen as ugen
import utils.err_codes as uerr

if ty.TYPE_CHECKING:
    import io

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} [flag]",
    summary="Access the Quark history",
    details=(
        "ARGUMENTS",
        ("none", ""),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("-d, --remove-duplicates", "Remove duplicates in the history file"),
        ("-c, --clear", "Clear history"),
        ("-s, --size", "Display size of the history file"),
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=0,
    opts=(),
    flags=(
        "-c", "--clear",
        "-d", "--remove-duplicates",
        "-s", "--size"
    )
)


def ld_hist_fl(mode: str = "r") -> "io.TextIOBase | int":
    try:
        return open(uconst.HIST_FL, mode)
    except FileNotFoundError:
        ugen.err("No history file: \"{uconst.HIST_FL}\"")
        return uerr.ERR_FL_404
    except PermissionError:
        ugen.err(f"Access denied: \"{uconst.HIST_FL}\"")
        return uerr.ERR_PERM_DENIED
    except IsADirectoryError:
        ugen.err(f"Is a directory: \"{uconst.HIST_FL}\"")
        return uerr.ERR_IS_A_DIR
    except OSError as e:
        ugen.err(f"OS error; {e.strerror}")
        return uerr.ERR_OS_ERR


def run(data: ugen.CmdData) -> int:
    clear_hist = "-c" in data.flags or "--clear" in data.flags
    rm_dupls = "-d" in data.flags or "--remove-duplicates" in data.flags
    get_sz = "-s" in data.flags or "--size" in data.flags

    if clear_hist:
        f = ld_hist_fl(mode="w")
        if isinstance(f, int):
            return f

    if rm_dupls:
        uniq = []
        f = ld_hist_fl(mode="r")
        if isinstance(f, int):
            return f
        for ln in f.readlines():
            if ln not in uniq:
                uniq.append(ln)
        f.close()

        g = ld_hist_fl(mode="w")
        if isinstance(g, int):
            return g
        to_write = "".join(uniq)
        g.write(to_write + ("" if to_write.endswith("\n") else "\n"))
        g.close()

    if get_sz:
        ugen.write(str(pl.Path(uconst.HIST_FL).stat().st_size) + "\n")

    if not (get_sz or rm_dupls):
        f = ld_hist_fl(mode="r")
        if isinstance(f, int):
            return f
        ugen.write(f.read())
        f.close()

    return uerr.ERR_ALL_GOOD
