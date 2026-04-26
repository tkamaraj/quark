import os

import utils.err_codes as uerr
import utils.gen as ugen


CMD_SPEC = ugen.CmdSpec(min_args=0, max_args=0, opts=(), flags=())
HELP = ugen.HelpObj()


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    return err_code
