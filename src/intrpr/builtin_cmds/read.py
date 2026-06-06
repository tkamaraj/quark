import builtins

import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} [opt] ident [type]",
    summary="Read input into variable",
    details=(
        "ARGUMENTS",
        ("ident", "Identifier to read input into"),
        ("type", "Builtin type to cast value into"),
        "OPTIONS",
        ("-p, --prompt", "Prompt text"),
        "FLAGS",
        ("-g, --getch", "Get a single character immediately")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=1,
    max_args=2,
    opts=("-p", "--prompt"),
    flags=("-g", "--getch")
)

ERR_NO_SUCH_BUILTIN_TYP = 1000
ERR_INV_VAL_FOR_TYP = 1001


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    prompt = ""
    single_chr = False
    ident = data.args[0]
    typ = data.args[1] if len(data.args) == 2 else None

    for flag in data.flags:
        if flag in ("-g", "--getch"):
            single_chr = True

    for opt, val in data.opts.items():
        if opt in ("-p", "--prompt"):
            prompt = val

    if typ is None:
        var_obj = str
    else:
        for nm, obj in vars(builtins).items():
            if nm == typ:
                var_obj = obj
                found = True
                break
        else:
            ugen.err(f"No such type in scope: '{typ}'", nm=data.cmd_nm)
            return ERR_NO_SUCH_BUILTIN_TYP

    ugen.write(prompt, flush=True)
    if single_chr:
        inp_hdlr = ugen.InpHdlr()
        inp_hdlr.set_new_sett()
        try:
            inp = inp_hdlr.getch()
        finally:
            inp_hdlr.reset_sett()
        ugen.write("\n")
    else:
        inp = input()
    try:
        to_set = var_obj(inp)
        data.intrpr_vars[ident] = to_set
    except ValueError:
        err_code = ERR_INV_VAL_FOR_TYP
        ugen.err(f"Invalid value for type '{typ}': '{inp}'")

    return err_code
