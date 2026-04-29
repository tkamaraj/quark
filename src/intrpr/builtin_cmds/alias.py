import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} -E [name ...]",
    summary="Inspect aliases",
    details=(
        "ARGUMENTS",
        ("name", "Name of alias to fetch"),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("none", "")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    opts=(),
    flags=()
)

ERR_INV_ALIAS = 1000
ERR_UNK_ALIAS = 1001


def run(data: ugen.CmdData) -> int:
    to_write: list[tuple[str, str]]
    err_code = uerr.ERR_ALL_GOOD
    alias_dict = data.env_vars.get("_ALIASES_")
    max_len = 0
    to_write = []

    if not data.args:
        for i, alias in enumerate(alias_dict):
            alias_val = alias_dict[alias]
            if not isinstance(alias, str) or not isinstance(alias_val, str):
                err_code = err_code or ERR_INV_ALIAS
                ugen.err(f"Invalid alias at pos {i} in _ALIASES_")
                continue
            escd_alias = ugen.esc_chrs(alias, extra=("=",))
            max_len = max(max_len, len(escd_alias))
            to_write.append((
                ugen.S.fmt(escd_alias, data.is_tty, ugen.S.green_4),
                "'" + alias_val + "'"
            ))

    else:
        for arg in data.args:
            if arg not in alias_dict:
                err_code = err_code or ERR_UNK_ALIAS
                ugen.err(f"Unknown alias: '{arg}'")
                continue
            alias_val = alias_dict[arg]
            if not isinstance(alias_val, str):
                err_code = err_code or ERR_INV_ALIAS
                ugen.err(f"Invalid alias '{arg}'")
                continue
            escd_arg = "'" + ugen.esc_chrs(arg, extra=("=",))
            max_len = max(max_len, len(escd_arg))
            to_write.append((
                ugen.S.fmt(escd_arg, data.is_tty, ugen.S.green_4),
                "'" + alias_val + "'"
            ))

    # For the quotes that'll surround the name
    max_len += 2
    pad_fn = ugen.ljust if data.is_tty else (lambda s, amt: s)
    for i in to_write:
        ugen.write(
            pad_fn("'" + i[0] + "'", max_len)
            + (" = " if data.is_tty else "=")
            + i[1]
            + "\n"
        )

    return err_code
