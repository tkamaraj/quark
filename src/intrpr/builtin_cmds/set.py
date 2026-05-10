import ast
import builtins
import os
import typing as ty

import src.utils.gen as ugen
import src.utils.consts as uconst
import utils.err_codes as uerr

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
    flags=("-r")
)

ERR_NO_SUCH_BUILTIN_TYP = 1000
ERR_INV_VAL_FOR_TYP = 1001
ERR_TXT_SYN_ERR = 1002
ERR_EXPD_ARGS = 1000
ERR_NO_SUCH_VAR = 1001
ERR_VAR_EXISTS = 1002


class NoTypSpecified:
    pass


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
            if arg not in data.env_vars:
                err_code = err_code or ERR_NO_SUCH_VAR
                ugen.err(f"No such variable: '{arg}'")
                continue
            data.env_vars.rm(arg, complain)

    else:
        if len(data.args) not in (2, 3):
            ugen.err("Expected 2 or 3 arguments to set variable")
            return ERR_EXPD_ARGS

        var_nm = data.args[0]
        var_val = data.args[1]
        var_typ = data.args[2] if len(data.args) == 3 else "str"
        for nm, obj in vars(builtins).items():
            if nm == var_typ:
                var_obj = obj
                found = True
                break
        else:
            ugen.err(f"No such type in scope: '{var_typ}'")
            return ERR_NO_SUCH_BUILTIN_TYP

        # There's a problem with this code segment. What happens is that
        # ast.literal_eval raises a ValueError when trying to evaluate a string
        # literal. Like, say this: `set _PTH_ foo str`. This raises a
        # ValueError, and thus control falls into the except block, which
        # produces a misleading error message, even though the value was
        # perfectly OK
        # OK, I checked, and you need quotes around the literal to be evaluated
        # as a string. Not quotes in the interpreter raw input line. Escaped
        # quotes.
        # TODO: Check and resolve this
        try:
            var_val = var_obj(ast.literal_eval(var_val))
        except ValueError:
            ugen.err(f"Illegal value for type '{var_typ}': '{var_val}'")
            return ERR_INV_VAL_FOR_TYP
        except SyntaxError:
            ugen.err("Syntax error: invalid text")
            return ERR_TXT_SYN_ERR
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()

        try:
            if complain and var_nm in data.env_vars:
                ugen.err("Variable exists: '{var_nm}'")
                err_code = ERR_VAR_EXISTS
            else:
                data.env_vars.set(var_nm, var_val, complain)
        except ugen.InvVarTypErr:
            err_code = uerr.ERR_ENV_VAR_INV_TYP
            ugen.err(
                f"Invalid type for '{var_nm}': '{var_val.__class__.__name__}'"
            )
        except ugen.InvVarNmErr:
            err_code = uerr.ERR_ENV_VAR_INV_NM
            ugen.err(f"Invalid variable name: '{var_nm}'")
        except ugen.UnkVarErr:
            err_code = uerr.ERR_ENV_UNK_VAR
            ugen.err(f"Unknown variable: '{var_nm}'")

    return err_code
