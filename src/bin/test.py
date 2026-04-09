import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=CMD_NM,
    summary="Just a test command",
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
    ugen.write(data.stdin)
    return uerr.ERR_ALL_GOOD
