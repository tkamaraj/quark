import builtins
import os
import typing as ty

import utils.gen as ugen
import utils.consts as uconst
import utils.err_codes as uerr
if ty.TYPE_CHECKING:
    import intrpr.internals as iint

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} name value [type]",
    summary="Set an interpreter variable",
    details=(
        "ARGUMENTS",
        ("name", "Variable name"),
        ("value", "Variable value"),
        ("type", "Variable type (Python built-in type)"),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("-r, --remove", "Remove a variable"),
        (
            "-c, --complain",
            "Complain when name doesn't exist for -r/--remove, and when name exists otherwise"
        )
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=1,
    max_args=float("inf"),
    opts=(),
    flags=(
        "-r", "--remove",
        "-c", "--complain"
    )
)

ERR_NO_SUCH_BUILTIN_TYP = 1000
ERR_INV_VAL_FOR_TYP = 1001
ERR_TXT_SYN_ERR = 1002
ERR_EXPD_ARGS = 1000
ERR_NO_SUCH_VAR = 1001
ERR_VAR_EXISTS = 1002


class NoTypSpecified:
    pass


def set_vars_helper(
    cmd_nm: str,
    var_nm: str,
    var_typ: str,
    var_val: str,
    complain: bool,
    intrpr_vars: "iint.IntrprTbl"
) -> int:
    err_code = uerr.ERR_ALL_GOOD

    # If no 3rd argument, type is assumed str, and var_val remains the same
    # 3rd argument passed; type was specified as "None"
    if var_typ == "None":
        if var_val != "None":
            ugen.err(
                f"Invalid value for '{var_typ}': '{var_val}'",
                nm=cmd_nm
            )
        var_val = None
    # 3rd argument passed; type was specified
    elif var_typ != None:
        for nm, obj in vars(builtins).items():
            if nm == var_typ:
                var_obj = obj
                found = True
                break
        else:
            ugen.err(f"No such type in scope: '{var_typ}'", nm=cmd_nm)
            return ERR_NO_SUCH_BUILTIN_TYP
        try:
            var_val = var_obj(var_val)
        except ValueError:
            ugen.err(
                f"Illegal value for type '{var_typ}': '{var_val}'",
                nm=cmd_nm
            )
            return ERR_INV_VAL_FOR_TYP
        # except SyntaxError:
        #     ugen.err("Syntax error: invalid text")
        #     return ERR_TXT_SYN_ERR

    try:
        if complain and var_nm in intrpr_vars:
            ugen.err("Variable exists: '{var_nm}'", nm=cmd_nm)
            err_code = ERR_VAR_EXISTS
        else:
            intrpr_vars.set(var_nm, var_val)
    except ugen.InvVarTypErr:
        err_code = uerr.ERR_ENV_VAR_INV_TYP
        ugen.err(
            f"Invalid type for '{var_nm}': '{var_val.__class__.__name__}'",
            nm=cmd_nm
        )
    except ugen.InvVarNmErr:
        err_code = uerr.ERR_ENV_VAR_INV_NM
        ugen.err(f"Invalid variable name: '{var_nm}'", nm=cmd_nm)
    except ugen.UnkVarErr:
        err_code = uerr.ERR_ENV_UNK_VAR
        ugen.err(f"Unknown variable: '{var_nm}'", nm=cmd_nm)

    return err_code


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    rm = False
    complain = False

    for flag in data.flags:
        if flag in ("-r", "--remove"):
            rm = True
        elif flag in ("-c", "--complain"):
            complain = True

    if rm:
        for arg in data.args:
            if complain and arg not in data.intrpr_vars:
                err_code = err_code or ERR_NO_SUCH_VAR
                ugen.err(f"No such variable: '{arg}'", nm=data.cmd_nm)
                continue
            data.intrpr_vars.rm(arg)

    else:
        if len(data.args) not in (2, 3):
            ugen.err(
                "Expected 2 or 3 arguments to set variable",
                nm=data.cmd_nm
            )
            return ERR_EXPD_ARGS

        var_nm = data.args[0]
        var_val = data.args[1]
        var_typ = data.args[2] if len(data.args) == 3 else None
        tmp_err_code = set_vars_helper(
            data.cmd_nm,
            var_nm,
            var_typ,
            var_val,
            complain,
            data.intrpr_vars
        )
        err_code = err_code or tmp_err_code

    return err_code
