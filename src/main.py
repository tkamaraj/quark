#!/usr/bin/env -S python3 -BOO

import collections as collns
# import logging as lg
import os
import re
# import readline as rl
import select as sel
import signal as sig
import sys
import termios
import traceback as tb
import tty
import typing as ty

import intrpr.cfg_mgr as cmgr
import intrpr.eng as ieng
import utils.consts as uconst
import utils.err_codes as uerr
import utils.gen as ugen
import logger.eng as leng

if not sys.argv:
    called_nm = "[main]"
else:
    called_nm = sys.argv[0]
    # Nuitka overwrites sys.argv[0]
    if "__compiled__" in locals():
        called_nm = __compiled__.original_argv0

MIN_ARGS = 0
MAX_ARGS = 1
VALID_OPTS = {}
VALID_FLAGS = {}

# TODO: Update the help string
HELP_TXT = f"""USAGE
  {called_nm} [flag ...] [opt] [fl]
ARGUMENTS
  fl          Script to run
OPTIONS
  -t, --debug-time-unit unit
              Unit for debugging time output
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
    ln_mode: str
    pre_ld_ext_cmds: bool
    stdout_ansi: bool
    stderr_ansi: bool
    log_lvl: int
    debug_time_expo: int


def parse_argv(passed_params: list[str]) -> MainProgParsed:
    len_passed_params = len(passed_params)
    skip = 0

    ln_mode = "default"
    pre_ld_ext_cmds = False
    stdout_ansi = False
    stderr_ansi = False
    log_lvl = leng.LogLvls.WARN
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
            log_lvl = leng.LogLvls.DEBUG
        elif param in ("-po", "--preserve-ANSI-stdout"):
            stdout_ansi = True
        # Flag: Preserve ANSI colour codes in STDERR redirects
        elif param in ("-pe", "--preserve-ANSI-stderr"):
            stderr_ansi = True
        # Flag: Show info
        elif param in ("-i", "--info"):
            log_lvl = leng.LogLvls.INFO
        # Flag: No warnings
        elif param in ("-W", "--no-warnings"):
            if log_lvl <= leng.LogLvls.WARN:
                log_lvl = leng.LogLvls.ERR
        elif param in ("-h", "--help"):
            ugen.write(HELP_TXT)
            sys.exit(uerr.ERR_ALL_GOOD)
        elif param == "--line-mode":
            # No value for option
            if i == len_passed_params - 1:
                ugen.err_Q("Expected value for '{param}'")
                sys.exit(uerr.ERR_MP_EXPD_VAL_OPT)
            val = passed_params[i + 1]
            if val not in ("emacs", "vi", "raw"):
                ugen.err_Q(f"Invalid value for '{param}': '{val}'")
                sys.exit(uerr.ERR_MP_INV_VAL)
            ln_mode = val
        # Option: Debug time unit conversion exponent
        elif param in ("-t", "--debug-time-unit"):
            # No value for the option found...
            if i == len_passed_params - 1:
                ugen.err_Q(f"Expected value for '{param}'")
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
                ugen.err_Q(f"Invalid value for '{param}': '{val}'")
                sys.exit(uerr.ERR_MP_INV_VAL)
            skip += 1
        else:
            ugen.err_Q(f"Unknown parameter: '{param}'")
            sys.exit(uerr.ERR_MP_UNK_TOK)

    return MainProgParsed(
        ln_mode=ln_mode,
        pre_ld_ext_cmds=pre_ld_ext_cmds,
        stdout_ansi=stdout_ansi,
        stderr_ansi=stderr_ansi,
        log_lvl=log_lvl,
        debug_time_expo=debug_time_expo
    )


def main() -> None:
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
        log_fd = open(uconst.LOG_FL, "a")
        leng.set_log_lvl(parsed_params.log_lvl)
        lgrs = leng.LgrVessel(
            leng.Lgr("lgr_c", "C", parsed_params.log_lvl, sys.stderr),
            leng.Lgr("lgr_q", "Q", parsed_params.log_lvl, sys.stderr),
            leng.Lgr("fl_lgr", "F", leng.LogLvls.CRIT, log_fd)
        )
        # Recommended not to put any debug, info or warning statements above
        # this, because even though those functions can handle loggers not
        # being initialised, they do not obey the log levels, because log
        # levels aren't available before the following line
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
        ugen.info_Q(f"running from \"{uconst.RUN_PTH}\"")
        # No line mode option passed from command line
        if parsed_params.ln_mode == "default":
            if cfg.ln_mode != "raw":
                import readline as rl
                rl.parse_and_bind("tab: complete")
                if cfg.ln_mode == "vi":
                    rl.parse_and_bind("set editing-mode vi")
        # Line mode option passed from command line
        elif parsed_params.ln_mode != "raw":
            import readline as rl
            rl.parse_and_bind("tab: complete")
            if parsed_params.ln_mode == "vi":
                rl.parse_and_bind("set editing-mode vi")

    except Exception as e:
        tb.print_exc()
        ugen.fatal_Q(
            f"Interpreter init failed; {e.__class__.__name__}",
            uerr.ERR_UNK_FATAL,
            exc_txt=tb.format_exc(),
        )

    prompt_404_warned = False
    while True:
        try:
            try:
                prompt = intrpr.env_vars.get("_PROMPT_")
                prompt_404_warned = False
            except ugen.UnkVarErr:
                if not prompt_404_warned:
                    ugen.warn_Q("_PROMPT_ not found; using default")
                prompt = uconst.Defaults.PROMPT
                prompt_404_warned = True
            raw_ln = input(intrpr.reslv_prompt(prompt))
            cmd_ret = intrpr.exec(raw_ln)
            intrpr.env_vars.set("_LAST_RET_", str(cmd_ret))
            ugen.debug(str(intrpr.intrpr_vars))

        # ^c on a built-in command
        except KeyboardInterrupt:
            intrpr.env_vars.set("_LAST_RET_", str(uerr.ERR_KB_INTERR))
            ugen.write("\n")

        # ^c on an external command
        except ugen.KeyboardInterruptWPrevileges as e:
            intrpr.env_vars.set("_LAST_RET_", str(uerr.ERR_KB_INTERR))
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
