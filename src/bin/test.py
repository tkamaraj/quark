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
    full = 10 ** 8
    segment = full // 5
    for j, i in enumerate(range(segment, full, segment)):
        ugen.write(str(j) * i)
        x = " " * 10 ** 10
    return uerr.ERR_ALL_GOOD
