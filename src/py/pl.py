import os
import re
import typing as ty

from src.utils import err_codes as uerr
from src.utils import gen as ugen

OPTS = {
    "FIELDS": ("-f", "--fields"),
}
FLAGS = {
    "ESC"       : ("-e", "--escape"),
    "EXACT"     : ("-x", "--exact"),
    "LONG"      : ("-l", "--long"),
    "NO_HEADERS": ("-H", "--no-headers"),
}

VALID_FIELDS = {
    "pid"      : "Process PID",
    "ppid"     : "Parent PID",
    "name"     : "Process name",
    "threads"  : "Threads used by process",
    "starttime": "Start time of process",
    "full"     : "Full invokation",
}
CMD_NM = __name__.split(".")[-1]

# TODO: Don't forget to update the help string
HELP = ugen.HelpObj(
    usage=f"{CMD_NM} [flag ...] [opt val ...] [proc ...]",
    summary="Get a list of running processes",
    details=(
        "ARGUMENTS",
        (
            "proc",
            "Regex to match with process names, unless -e/--exact is given"
        ),
        "OPTIONS",
        (
            "-f, --fields FIELD[,FIELD...]",
            f"Fields to display\nValid values: {", ".join(VALID_FIELDS)}",
        ),
        "FLAGS",
        ("-l, --long", "Alias for `--fields pid,full`"),
        ("-e, --escape", "Escape regex strings"),
        ("-x, --exact", "Exactly match arguments")
    )
)

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    opts=tuple(opt for opts in OPTS.values() for opt in opts),
    flags=tuple(flag for flags in FLAGS.values() for flag in flags)
)


def rd_fl_as_bin(fl_pth: str) -> str | int:
    try:
        with open(fl_pth, "rb") as f:
            cntnt = f.read()
            return cntnt.decode()
    except PermissionError:
        return uerr.ERR_PERM_DENIED
    except FileNotFoundError:
        return uerr.ERR_FL_404
    except IsADirectoryError:
        return uerr.ERR_IS_A_DIR
    except OSError:
        return uerr.ERR_OS_ERR


def run(data: ugen.CmdData) -> int:
    err_code = uerr.ERR_ALL_GOOD
    fields = ["pid", "name"]
    wrt_headers = True
    match_exact = False

    for flag in data.flags:
        if flag in FLAGS["NO_HEADERS"]:
            wrt_headers = False
        elif flag in FLAGS["LONG"]:
            fields = ["pid", "full"]

    for opt, val in data.opts.items():
        if opt in OPTS["FIELDS"]:
            fields = list(dict.fromkeys(val.split(",")))
            if inv := [i for i in fields if i not in VALID_FIELDS]:
                ugen.err(
                    f"Invalid value(s) for fields: "
                    + ", ".join(("'" + ugen.esc_chrs_all(i) + "'") for i in inv)
                )
                return uerr.ERR_INV_VAL_OPT

    proc_arr = {k: [] for k in fields}
    max_lens = {k: 0 for k in fields}
    max_pid_len = 0
    max_ppid_len = 0
    max_num_threads_len = 0
    max_starttime_len = 0
    max_nm_len = 0
    max_full_len = 0
    cnt = 0

    for i in os.scandir("/proc"):
        if not i.name.isnumeric():
            continue

        pid = i.name
        ppid = "?"
        name = "?"
        threads = "?"
        starttime = "?"
        full = "???"

        cmdline = rd_fl_as_bin(os.path.join(i.path, "cmdline"))
        if isinstance(cmdline, int):
            ugen.warn(f"Cannot obtain full command line: {pid}")
        else:
            full = cmdline.replace("\x00", " ")

        stat = rd_fl_as_bin(os.path.join(i.path, "stat"))
        if isinstance(stat, int):
            ugen.warn(f"Cannot obtain process status: {pid}")
        else:
            stat = re.search(r"(.+)\s+\((.+)\)\s+(.+)", stat)
            stat_rt_part = stat.group(3).split()
            name = stat.group(2)
            ppid = stat_rt_part[1]
            threads = stat_rt_part[17]
            starttime = stat_rt_part[19]

        for field in fields:
            # Feel like this is going to bite me in the ass someday...
            proc_arr[field].append(locals()[field])
            max_lens[field] = max(max_lens[field], len(locals()[field]))
        cnt += 1

    # TODO: add right alignment for specific fields, like PID, PPID, etc.

    fields_len = len(fields)

    if wrt_headers and cnt > 0:
        tmp = []
        for i, field in enumerate(fields):
            pad_amt = max_lens[field]
            tmp.append(
                ugen.ljust(field.upper(), amt=pad_amt)
                if i < fields_len - 1 else field.upper()
            )
        tmp_joined = "  ".join(tmp) + "\n"
        # If no terminal size is available or output is not to TTY or length of
        # whole line is less than total available columns, use whole line as it is
        if (
            data.term_sz is None
            or not data.is_tty
            or len(tmp_joined) <= data.term_sz.columns
        ):
            ugen.write(tmp_joined)
        # Otherwise chop off
        else:
            ugen.write(tmp_joined[: data.term_sz.columns - 1] + ">")

    final = []
    for i in range(cnt):
        cur = []
        for j, field in enumerate(fields):
            field_i = proc_arr[field][i]
            pad_amt = max_lens[field]
            cur.append(
                ugen.ljust(field_i, amt=pad_amt) if j < fields_len - 1 else field_i
            )
        cur_joined = "  ".join(cur)
        # If no terminal size is available or output is not to TTY or length of
        # whole line is less than total available columns, use whole line as it is
        if (
            data.term_sz is None
            or not data.is_tty
            or len(cur_joined) <= data.term_sz.columns
        ):
            final.append(cur_joined)
        # Otherwise, chop off
        else:
            final.append(cur_joined[: data.term_sz.columns - 1] + ">")

    ugen.write("\n".join(final) + "\n")
    return err_code
