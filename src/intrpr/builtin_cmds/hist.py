import io
import pathlib as pl

import utils.consts as uconst
import utils.gen as ugen
import utils.err_codes as uerr

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
        ("-s, --size", "Display size of the history file"),
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=0,
    opts=(),
    flags=(
        "-s", "--size",
        "-d", "--remove-duplicates"
    )
)


def ld_hist_fl(mode: str = "r") -> io.TextIO | int:
    try:
        return open(uconst.HIST_FL, mode)
    except FileNotFoundError:
        ugen.err("No history file: \"{uconst.HIST_FL}\"")
        return uerr.ERR_FL_404
    except PermissionError:
        ugen.err(f"Access denied: \"{uconst.HIST_FL}\"")
        return uerr.ERR_PERM_DENIED
    except OSError as e:
        ugen.err(f"OS error; {e.strerror}: \"{uconst.HIST_FL}\"")
        return uerr.ERR_OS_ERR
    except Exception:
        return uerr.ERR_UNK_ERR


def run(data: ugen.CmdData) -> int:
    get_sz = "-s" in data.flags or "--size" in data.flags
    rm_dupls = "-d" in data.flags or "--remove-duplicates" in data.flags

    if rm_dupls:
        f = ld_hist_fl(mode="r")
        uniq = []
        for ln in f.readlines():
            if ln not in uniq:
                uniq.append(ln)
        f.close()
        g = ld_hist_fl(mode="w")
        g.write("\n".join(uniq) + "\n")
        g.close()

    if get_sz:
        ugen.write(str(pl.Path(uconst.HIST_FL).stat().st_size) + "\n")

    if not (get_sz or rm_dupls):
        f = ld_hist_fl(mode="r")
        ugen.write(f.read())
        f.close()

    return uerr.ERR_ALL_GOOD
