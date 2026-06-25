import os
import typing as ty

import utils.gen as ugen
import utils.consts as uconst
import utils.err_codes as uerr
if ty.TYPE_CHECKING:
    import intrpr.internals as iint

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=(
        f"{CMD_NM} list\n"
        f"{CMD_NM} get name [...]\n"
        f"{CMD_NM} set name value\n"
        f"{CMD_NM} remove name [...]\n"
    ),
    summary="Manage environment variables",
    details=(
        "SUBCOMMANDS",
        ("-", "List all variables"),
        ("list", "List all variables"),
        ("get", "Get variables by name"),
        ("set", "Set variables"),
        ("remove", "Remove variables"),
        "ARGUMENTS",
        ("name", "Variable name"),
        ("value", "Variable value"),
        "OPTIONS",
        ("none", ""),
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    parse_sub_cmds=True,
    sub_cmds={
        None    : (0, 0),
        "set"   : (2, 2),
        "get"   : (1, float("inf")),
        "list"  : (0, 0),
        "remove": (1, float("inf"))
    },
    opts=(),
    flags=("-r", "--repr")
)

ERR_INV_VAL_FOR_TYP = 1000
ERR_TXT_SYN_ERR = 1001
ERR_EXPD_ARGS = 1002
ERR_NO_SUCH_VAR = 1003
ERR_VAR_EXISTS = 1004


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    repr_val = False

    if data.sub_cmd is None or data.sub_cmd == "list":
        max_nm_len = (
            len(max((i for i in data.env_vars), key=len))
            if data.env_vars else 0
        )
        for (nm, val) in data.env_vars:
            ugen.write(
                f"{nm:<{max_nm_len}} = {repr(val) if repr_val else val}\n"
            )

    elif data.sub_cmd == "get":
        max_arg_len = len(max(data.args, key=len)) if data.args else 0
        for arg in data.args:
            if arg not in data.env_vars:
                ugen.err(f"No such variable: '{arg}'", nm=data.cmd_nm)
                err_code = err_code or uerr.ERR_ENV_UNK_VAR
                continue
            val = data.env_vars[arg]
            ugen.write(
                f"{arg:<{max_arg_len}} = {repr(val) if repr_val else val}\n"
            )

    elif data.sub_cmd == "set":
        data.env_vars[data.args[0]] = data.args[1]

    elif data.sub_cmd == "remove":
        for arg in data.args:
            if arg not in data.env_vars:
                ugen.err(f"No such variable: '{arg}'", nm=data.cmd_nm)
                err_code = err_code or uerr.ERR_ENV_UNK_VAR
                continue
            data.intrpr_vars.rm(arg)

    return err_code
