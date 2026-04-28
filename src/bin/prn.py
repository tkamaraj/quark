import math
import pathlib as pl
import re

import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} fl ...",
    summary="Dump file content",
    details=(
        "ARGUMENTS",
        ("fl", "File to dump")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=1,
    max_args=math.inf,
    opts=(),
    flags=("-l", "--line-numbers")
)


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    ln_nums = "-l" in data.flags or "--line-numbers" in data.flags

    for arg in data.args:
        fl = pl.Path(arg).expanduser().absolute().resolve()
        try:
            with open(fl) as f:
                fl_cntnt = f.read()
        except FileNotFoundError:
            ugen.err(f"No such file: \"{arg}\"")
            err_code = err_code or uerr.ERR_FL_404
            continue
        except PermissionError:
            ugen.err(f"Access denied: \"{arg}\"")
            err_code = err_code or uerr.ERR_PERM_DENIED
            continue
        except IsADirectoryError:
            ugen.err(f"Is a directory: \"{arg}\"")
            err_code = err_code or uerr.ERR_IS_A_DIR
            continue
        except OSError as e:
            err_code = err_code or uerr.ERR_OS_ERR
            ugen.err(f"OS error; {e.strerror}")
            continue

        if not ln_nums:
            ugen.write(
                ugen.S.fmt(arg, data.is_tty, ugen.S.green_4)
                + "\n"
                + fl_cntnt
            )
        else:
            lns = fl_cntnt.splitlines()
            len_ln_cnt = len(str(len(lns)))
            ugen.write(
                ugen.S.fmt(arg, data.is_tty, ugen.S.green_4) + "\n"
                + "".join(
                    f"{i:>{len_ln_cnt}}  {j}\n" for i, j in enumerate(lns)
                )
            )

    return err_code

