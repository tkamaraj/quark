import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=CMD_NM,
    summary=f"Just returns {uerr.ERR_FALSE}",
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
    return uerr.ERR_FALSE

