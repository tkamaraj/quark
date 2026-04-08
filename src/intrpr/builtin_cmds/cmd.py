import subprocess as sp

import utils.gen as ugen
import utils.err_codes as uerr

HELP = ugen.HelpObj(
    usage="cmd arg [...]",
    summary="Execute strings in the system shell",
    details=(
        "ARGUMENTS",
        ("arg", "Part of line to be executed in the system shell"),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("none", ""),
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=1,
    max_args=float("inf"),
    opts=(),
    flags=()
)

ERR_CMD_NOT_SUCCESS = 1000


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD

    compd_proc = sp.run(data.args, shell=True, capture_output=True, text=True)
    if compd_proc.returncode != 0:
        err_code = ERR_CMD_NOT_SUCCESS

    if compd_proc.stderr:
        ugen.err(compd_proc.stderr)
    ugen.write(compd_proc.stdout)
    return err_code
