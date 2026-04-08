import socket

import utils.err_codes as uerr
import utils.gen as ugen

HELP = ugen.HelpObj(
    usage="host",
    summary="Get hostname of the machine",
    details=(
        "ARGUMENTS",
        ("none", ""),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("none", "")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=0,
    opts=(),
    flags=()
)


def run(data: ugen.CmdData) -> int:
    ugen.write(socket.getfqdn() + "\n")
    return uerr.ERR_ALL_GOOD
