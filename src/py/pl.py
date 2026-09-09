import os
import re
import typing as ty

from src.utils import err_codes as uerr
from src.utils import gen as ugen

CMD_NM = __name__.split(".")[-1]

# TODO: Don't forget to update the help string
HELP = ugen.HelpObj(
    usage=f"{CMD_NM} [flag ...] [proc ...]",
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

# TODO: Don't forget to update the spec
CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    opts=("-f", "--fields"),
    flags=(
        "-H", "--no-headers",
        "-l", "--long",
    )
)


def rd_fl(fl_pth: str, binary: bool = False) -> str | int:
    try:
        with open(fl_pth, "rb" if binary else "r") as f:
            cntnt = f.read()
            if isinstance(cntnt, bytes):
                return cntnt.decode()
            return cntnt
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
    long = False
    fields = ["pid", "name"]
    wrt_headers = True
    valid_fields = ["pid", "ppid", "name", "threads", "starttime", "full"]

    for opt, val in data.opts.items():
        if opt in ("-f", "--fields"):
            fields = val.split(",")
            if inv := [i for i in fields if i not in valid_fields]:
                ugen.err(
                    f"Invalid value(s) for fields: "
                    + ", ".join(("'" + ugen.esc_chrs_all(i) + "'") for i in inv)
                )
                return uerr.ERR_INV_VAL_OPT

    for flag in data.flags:
        if flag in ("-H", "--no-headers"):
            wrt_headers = False
        if flag in ("-l", "--long"):
            fields = ["pid", "full"]

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

        cmdline = rd_fl(os.path.join(i.path, "cmdline"), binary=True)
        if isinstance(cmdline, int):
            ugen.warn(f"Cannot obtain full command line: {pid}")
        else:
            full = cmdline.replace("\x00", " ")

        stat = rd_fl(os.path.join(i.path, "stat"))
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

    if wrt_headers and cnt > 0:
        headers = [ugen.ljust(field.upper(), amt=max_lens[field]) for field in fields]
        ugen.write("  ".join(headers) + "\n")

    final = []
    fields_len = len(fields)
    for i in range(cnt):
        cur = []
        for j, field in enumerate(fields):
            field_i = proc_arr[field][i]
            pad_amt = max_lens[field]
            cur.append(
                ugen.ljust(field_i, amt=pad_amt) if j < fields_len - 1 else field_i
            )
        cur_joined = "  ".join(cur)
        if (
            data.term_sz is None
            or not data.is_tty
            or len(cur_joined) <= data.term_sz.columns
        ):
            final.append("  ".join(cur))
        else:
            final.append("  ".join(cur)[: data.term_sz.columns - 1] + ">")

    ugen.write("\n".join(final) + "\n")
    return err_code
