import re
import subprocess as sp
import typing as ty

import utils.err_codes as uerr
import utils.gen as ugen

CMD_NM = __name__.split(".")[-1]

HELP = ugen.HelpObj(
    usage=f"{CMD_NM} [flag ...] proc ...",
    summary="Get a list of running processes",
    details=(
        "ARGUMENTS",
        (
            "proc",
            "Regex to match with process names, unless -e/--exact is given"
        ),
        "OPTIONS",
        ("none", ""),
        "FLAGS",
        ("-l, --long", "Process long listing"),
        ("-e, --escape", "Escape regex strings"),
        ("-x, --exact", "Exactly match arguments")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    opts=(),
    flags=(
        "-l", "--long",
        "-x", "--exact",
        "-e", "--escape"
    )
)

ERR_CANT_GET_PROC_LIST = 1000

T = ty.TypeVar("T")
tuple4 = tuple[T, T, T, T]
tuple7 = tuple[T, T, T, T, T, T, T]


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    long = False
    esc_patt = False
    exact_match = False

    for flag in data.flags:
        if flag in ("-l", "--long"):
            long = True
        elif flag in ("-e", "--escape"):
            esc_patt = True
        elif flag in ("-x", "--exact"):
            exact_match = True

    if long:
        ps_fmt_str = "uid,pid,ppid,psr,stime,time,cmd"
    else:
        ps_fmt_str = "pid,stime,time,comm"

    num_cols = ps_fmt_str.count(",")

    rn_cmd = ["ps", "-eo", ps_fmt_str, "--no-headers"]
    compd_proc = sp.run(rn_cmd, capture_output=True, text=True)
    if compd_proc.returncode != 0:
        ugen.err("Could not get process list")
        return ERR_CANT_GET_PROC_LIST
    stdout = compd_proc.stdout.splitlines()

    proc_list = []
    len_arr = []

    for ln in stdout:
        # https://docs.python.org/3.14/library/stdtypes.html#str.split
        # "If sep is not specified or is None, a different splitting algorithm
        # is applied: runs of consecutive whitespace are regarded as a single
        # separator, [...]"
        out = ln.split(None, maxsplit=num_cols)
        proc_list.append(tuple(out))
        len_arr.append(tuple(map(len, out)))

    if not data.args:
        # Determine the length of the longest element in each column.
        # Iterate over the lengths array, which is a list of tuples of containing
        # column length for each process
        max_len_arr = [0] * num_cols
        for j in range(num_cols):
            max_len_arr[j] = max(row[j] for row in len_arr)
        op_buf = proc_list

    else:
        matches = []
        seen = set()
        for arg in data.args:
            patt = arg if not esc_patt else re.escape(arg)
            # Var item is the whole row, i.e. the full process entry
            for i, item in enumerate(proc_list):
                if item in seen:
                    continue
                if not exact_match and re.match(patt, item[-1]) is None:
                    continue
                if exact_match and arg != item[-1]:
                    continue
                matches.append((i, item))
                seen.add(item)

        op_buf = [entry for _, entry in matches]
        # Populate max_len_arr with values
        max_len_arr = [0] * num_cols
        for j in range(num_cols):
            # max(...) raises ValueError if iterable is empty
            if not matches:
                break
            max_len_arr[j] = max(len_arr[idx][j] for idx, _ in matches)

    for proc_entry in op_buf:
        to_write = "  ".join(
            [
                (item.ljust(max_len_arr[j]) if j < num_cols - 1 else item)
                for j, item in enumerate(proc_entry)
            ]
        )
        if len(to_write) > data.term_sz.columns:
            ugen.write(to_write[: data.term_sz.columns - 1] + ">\n")
        else:
            ugen.write(to_write + "\n")

    return err_code
