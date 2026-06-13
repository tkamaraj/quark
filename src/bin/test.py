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


def high_mem() -> None:
    ugen.write(data.stdin)
    full = 10 ** 8
    segment = full // 5
    for j, i in enumerate(range(segment, full, segment)):
        ugen.write(str(j) * i)
        x = " " * 10 ** 10
    return None


def run(data: ugen.CmdData) -> int:
    data.env_vars["foo"] = "bar"
    # data.env_vars["haha"] = "hehe"
    # ugen.write(str(data.env_vars.cnt))
    # print(data.env_vars)
    ugen.write(data.env_vars["foo"] + "\n")
    return uerr.ERR_ALL_GOOD
