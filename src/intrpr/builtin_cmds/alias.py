import typing as ty

import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=(
        f"{CMD_NM} [name ...]\n"
        f"{CMD_NM} -s name val"
    ),
    summary="Inspect and edit aliases",
    details=(
        "ARGUMENTS",
        ("name", "Name of alias to fetch or set"),
        ("val", "Value of alias to set"),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("none", ""),
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    parse_sub_cmds=True,
    sub_cmds={None: (0, 0), "list": (0, float("inf")), "set": (2, 2)},
    opts=(),
    flags=()
)


class Out(ty.NamedTuple):
    alias: str
    val: str


class Err(ty.NamedTuple):
    msg: str


ERR_INV_ALIAS = 1000
ERR_UNK_ALIAS = 1001


def run(data: ugen.CmdData) -> int:
    to_write: list[tuple[str, str]]

    err_code = uerr.ERR_ALL_GOOD
    set_alias = False
    try:
        alias_dict = data.env_vars.get("_ALIASES_")
    except ugen.UnkVarErr:
        ugen.warn("Cannot find _ALIASES_; using empty dict")
        alias_dict = {}

    if data.sub_cmd == "list" or data.sub_cmd is None:
        max_len = 0
        to_write = []

        if len(data.args) == 0:
            for i, alias in enumerate(alias_dict):
                alias_val = alias_dict[alias]
                if not isinstance(alias, str) or not isinstance(alias_val, str):
                    err_code = err_code or ERR_INV_ALIAS
                    to_write.append(Err(f"Invalid alias at pos {i} in _ALIASES_"))
                    continue
                escd_alias = ugen.esc_chrs(alias, extra=("=",))
                max_len = max(max_len, len(escd_alias))
                to_write.append(Out(
                    ugen.S.fmt(escd_alias, data.is_tty, ugen.S.green_4),
                    "'" + alias_val + "'"
                ))
        else:
            for arg in data.args:
                if arg not in alias_dict:
                    err_code = err_code or ERR_UNK_ALIAS
                    to_write.append(Err(f"Unknown alias: '{arg}'"))
                    continue
                alias_val = alias_dict[arg]
                if not isinstance(alias_val, str):
                    err_code = err_code or ERR_INV_ALIAS
                    to_write.append(Err(f"Invalid alias '{arg}'"))
                    continue
                escd_arg = ugen.esc_chrs(arg, extra=("=",))
                max_len = max(max_len, len(escd_arg))
                to_write.append(Out(
                    ugen.S.fmt(escd_arg, data.is_tty, ugen.S.green_4),
                    "'" + alias_val + "'"
                ))

        # For the quotes that'll surround the name
        max_len += 2
        pad_fn = ugen.ljust if data.is_tty else (lambda s, amt: s)
        for i in to_write:
            if isinstance(i, Err):
                ugen.err(i.msg, nm=data.cmd_nm)
                continue
            ugen.write(
                pad_fn("'" + i.alias + "'", max_len)
                + (" = " if data.is_tty else "=")
                + f"{i.val}\n"
            )

    elif data.sub_cmd == "set":
        if len(data.args) < 2:
            ugen.err(
                f"Insufficient arguments; expected 2 args after subcommand, got {len(data.args)}",
                nm=data.cmd_nm
            )
            return uerr.ERR_INSUFF_ARGS
        elif len(data.args) > 2:
            ugen.err(
                f"Unexpected arguments; expected 2 after subcommand, got {len(data.args)}",
                nm=data.cmd_nm
            )
            return uerr.ERR_UNEXPD_ARGS
        alias_dict[data.args[0]] = data.args[1]
        data.env_vars.set("_ALIASES_", alias_dict)

    return err_code
