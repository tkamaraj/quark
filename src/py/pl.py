import os
import re
import typing as ty

from src.utils import err_codes as uerr
from src.utils import gen as ugen

CMD_NM = __name__.split(".")[-1]

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

CMD_SPEC = ugen.CmdSpec(
    min_args=0,
    max_args=float("inf"),
    opts=("-f", "--fields"),
    flags=()
)


class ProcEntry(ty.NamedTuple):
    pid: str    # PID is a str to eliminate unnecessary conversions
    nm: str
    full: str


def rd_fl(fl_pth: str, binary: bool = False) -> bytes:
    try:
        with open(fl_pth, "rb" if binary else "r") as f:
            return f.read()
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
    valid_fields = ["pid", "full", "ppid", "name", "threads", "starttime", "full"]

    for opt, val in data.opts.items():
        if opt in ("-f", "--fields"):
            comma_split = val.split(",")
            if inv := [i for i in comma_split if i not in valid_fields]:
                ugen.err(
                    f"Invalid value(s) for fields: "
                    + ", ".join(("'" + ugen.esc_chrs_all(i) + "'") for i in inv)
                )
                return uerr.ERR_INV_VAL_OPT
            fields = [*comma_split]

    for flag in data.flags:
        if flag in ("-H", "--no-headers"):
            wrt_headers = False

    proc_arr = []
    max_pid_len = 0
    max_ppid_len = 0
    max_num_threads_len = 0
    max_starttime_len = 0
    max_nm_len = 0
    max_full_len = 0

    for i in os.scandir("/proc"):
        if not i.name.isnumeric():
            continue

        pid = i.name
        prn_fields = dict.fromkeys(fields)
        prn_fields["pid"] = i.name
        prn_fields["full"] = "?"
        prn_fields["name"] = "?"
        prn_fields["ppid"] = "?"
        prn_fields["starttime"] = "?"
        prn_fields["full"] = "???"
        if "pid" in fields:
            max_pid_len = max(len(pid), max_pid_len)

        cmdline = rd_fl(os.path.join(i.path, "cmdline"), binary=True)
        if isinstance(cmdline, int):
            ugen.warn(f"Cannot obtain full command line: {pid}")
        else:
            prn_fields["full"] = cmdline.replace(b"\x00", b" ").decode()

        stat = rd_fl(os.path.join(i.path, "stat"))
        if isinstance(stat, int):
            ugen.warn(f"Cannot obtain process status: {pid}")
        else:
            stat = re.search(r"(.+)\s+\((.+)\)\s+(.+)", stat)
            stat_rt_part = stat.group(3).split()
            if "name" in fields:
                nm = stat.group(2)
                prn_fields["name"] = nm
                max_nm_len = max(len(nm), max_nm_len)
            if "ppid" in fields:
                ppid = stat_rt_part[1]
                prn_fields["ppid"] = ppid
                max_ppid_len = max(len(ppid), max_ppid_len)
            if "threads" in fields:
                num_threads = stat_rt_part[17]
                prn_fields["threads"] = num_threads
                max_num_threads_len = max(len(num_threads), max_num_threads_len)
            if "starttime" in fields:
                starttime = stat_rt_part[19]
                prn_fields["starttime"] = starttime
                max_starttime_len = max(len(starttime), max_starttime_len)

        proc_arr.append(prn_fields)

    if wrt_headers and proc_arr:
        # TODO: Add headers
        # ugen.write(f"{"PID":>{max_pid_len}} {"NAME":<{max_nm_len}}\n")
        pass

    # TODO: Space before first column needs to be removed when PID column is
    # TODO: NOT the first column
    for proc in proc_arr:
        ugen.write(
            (ugen.ljust(proc["pid"], max_pid_len) if "pid" in fields else "")
            + ((" " + ugen.ljust(proc["name"], max_nm_len)) if "name" in fields else "")
            + ((" " + ugen.ljust(proc["ppid"], max_ppid_len)) if "ppid" in fields else "")
            + ((" " + ugen.ljust(proc["threads"], max_num_threads_len)) if "threads" in fields else "")
            + ((" " + ugen.ljust(proc["starttime"], max_starttime_len)) if "starttime" in fields else "")
            + ((" " + ugen.ljust(proc["full"], max_full_len)) if "full" in fields else "")
            + "\n"
        )

    return err_code
