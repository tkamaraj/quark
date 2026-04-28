#!/usr/bin/env -S python3 -BOO

import collections as collns
import logging as lg
import os
import re
import select as sel
import signal as sig
import sys
import termios
import traceback as tb
import tty
import typing as ty

import intrpr.eng as ieng
import intrpr.cfg_mgr as cmgr
import utils.consts as uconst
import utils.err_codes as uerr
import utils.gen as ugen
import utils.loggers as ulog

if not sys.argv:
    called_nm = "[main]"
else:
    called_nm = sys.argv[0]

MIN_ARGS = 0
MAX_ARGS = 1
VALID_OPTS = {}
VALID_FLAGS = {}

HELP_TXT = f"""USAGE
  {called_nm} [flag ...] [fl]
ARGUMENTS
  fl          Script to run
OPTIONS
  -t, --debug-time-unit
              Set unit for debugging time output.
              Valid: 'ns', 'us', 'ms', 's'
FLAGS
  -d, --debug
              Show debug messages
  -e, --load-external
              Load all external commands on startup
  -h, --help  Display help text
  -i, --info  Show info messages
  -pe, --preserve-ANSI-stderr
              Preserve ANSI codes in STDERR redirects
  -po, --preserve-ANSI-stdout
              Preserve ANSI codes in STDOUT redirects
  -W, --no-warnings
              Suppress warnings
""".expandtabs(2)


class MainProgParsed(ty.NamedTuple):
    pre_ld_ext_cmds: bool
    stdout_ansi: bool
    stderr_ansi: bool
    log_lvl: int
    debug_time_expo: int


def parse_argv(passed_params: list[str]) -> MainProgParsed:
    """
    Parse parameters passed to the main program.

    :param passed_params: A list of strings, which is the passed parameters to
                        the main program.
    :type passed_params: list[str]

    :returns: An object that contains all the data that can be received from
              the arguments, options and flags that can be provided to the main
              program.
    :rtype: MainProgParsed
    """
    len_passed_params = len(passed_params)
    skip = 0

    pre_ld_ext_cmds = False
    stdout_ansi = False
    stderr_ansi = False
    log_lvl = ulog.WARN
    debug_time_expo = 6
    args = []

    for i, param in enumerate(passed_params):
        if skip:
            skip -= 1
            continue

        # Argument; has either an escaped hyphen at the front, or does not
        # start with an hyphen
        if param.startswith("\\-") or not param.startswith("-"):
            args.append(param)
            continue

        # Flag: preload external commands
        if param in ("-e", "--load-external"):
            pre_ld_ext_cmds = True
        # Flag: Show debug
        elif param in ("-d", "--debug"):
            log_lvl = ulog.DEBUG
        elif param in ("-po", "--preserve-ANSI-stdout"):
            stdout_ansi = True
        # Flag: Preserve ANSI colour codes in STDERR redirects
        elif param in ("-pe", "--preserve-ANSI-stderr"):
            stderr_ansi = True
        # Flag: Show info
        elif param in ("-i", "--info"):
            log_lvl = ulog.INFO
        # Flag: No warnings
        elif param in ("-W", "--no-warnings"):
            if log_lvl <= ulog.WARN:
                log_lvl = ulog.ERR
        elif param in ("-h", "--help"):
            ugen.write(HELP_TXT)
            sys.exit(uerr.ERR_ALL_GOOD)
        # Option: Debug time unit conversion exponent
        elif param in ("-t", "--debug-time-unit"):
            # No value for the option found...
            if i == len_passed_params - 1:
                ugen.err_Q(f"Expected value for '{param}'\n")
                sys.exit(uerr.ERR_MP_EXPD_VAL_OPT)
            val = passed_params[i + 1]
            if val == "ms":
                debug_time_expo = 6
            elif val == "us":
                debug_time_expo = 3
            elif val == "ns":
                debug_time_expo = 0
            elif val == "s":
                debug_time_expo = 9
            else:
                ugen.err_Q(f"Invalid value for '{param}': '{val}'\n")
                sys.exit(uerr.ERR_MP_INV_VAL)
            skip += 1
        else:
            ugen.err_Q(f"Unknown parameter: '{param}'\n")
            sys.exit(uerr.ERR_MP_UNK_TOK)

    return MainProgParsed(
        pre_ld_ext_cmds=pre_ld_ext_cmds,
        stdout_ansi=stdout_ansi,
        stderr_ansi=stderr_ansi,
        log_lvl=log_lvl,
        debug_time_expo=debug_time_expo
    )


def main() -> None:
    """
    """
    try:
        hist_fl = None
        try:
            hist_fl = open(uconst.HIST_FL, "a+")
        except PermissionError:
            ugen.warn_Q(f"Access denied: \"{uconst.HIST_FL}\"\n")
        except OSError as e:
            ugen.warn_Q(f"OS error; {e.strerror}\n")
        except Exception as e:
            ugen.warn_Q(
                f"Unknown error; ({e.__class__.__name__}) {e}; cannot write history\n"
            )

        parsed_params = parse_argv(sys.argv[1 :])
        lgrs = ulog.init_lgrs(
            parsed_params.log_lvl,
            parsed_params.log_lvl,
            ulog.CRIT
        )
        ugen.set_lgrs(lgrs)
        cfg = cmgr.get_cfg()
        intrpr = ieng.Intrpr(
            cfg=cfg,
            pre_ld_ext_cmds=parsed_params.pre_ld_ext_cmds,
            stdout_ansi=parsed_params.stdout_ansi,
            stderr_ansi=parsed_params.stderr_ansi,
            debug_time_expo=parsed_params.debug_time_expo,
            log_lvl=parsed_params.log_lvl
        )
        inp_hdlr = ugen.InpHdlr()
    except Exception as e:
        ugen.fatal_Q(
            f"During initialisation: {e.__class__.__name__}: {e}",
            uerr.ERR_UNK_FATAL,
            exc_txt=tb.format_exc()
        )

    while True:
        try:
            prompt = intrpr.env_vars.get("_PROMPT_")
            ugen.write(intrpr.reslv_prompt(prompt))
            hist_fl.seek(0)
            hist = hist_fl.read().splitlines()
            try:
                raw_ln = ugen.inp(inp_hdlr, hist=list(dict.fromkeys(hist)))
            finally:
                inp_hdlr.reset_sett()
            if raw_ln and hist_fl is not None:
                hist_fl.write(raw_ln + "\n")
                hist_fl.flush()
            cmd_ret = intrpr.exec(raw_ln)
            intrpr.env_vars.set("_LAST_RET_", cmd_ret)

        # ^c on a built-in command
        except KeyboardInterrupt:
            intrpr.env_vars.set("_LAST_RET_", uerr.ERR_KB_INTERR)
            ugen.write("\n")

        # ^c on an external command
        except ugen.KeyboardInterruptWPrevileges as e:
            intrpr.env_vars.set("_LAST_RET_", uerr.ERR_KB_INTERR)
            os.kill(e.child_pid, sig.SIGKILL)
            ugen.write("\n")

        except EOFError:
            ugen.write("\nbye\n")
            sys.exit(uerr.ERR_ALL_GOOD)

        except Exception as e:
            ugen.fatal_Q(
                f"{e.__class__.__name__} in main interpreter loop\n{e}",
                uerr.ERR_UNK_FATAL,
                exc_txt=tb.format_exc()
            )


if __name__ == "__main__":
    main()
