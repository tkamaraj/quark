import importlib.util as ilu
import inspect as ins
import io
import logging as lg
import multiprocessing as mp
import os
import pathlib as pl
import platform as pf
import pwd
import re
import struct as st
import sys
import time
import traceback as tb
import typing as ty

import intrpr.cfg_mgr as cmgr
import intrpr.cmd_reslvr as icrsr
import intrpr.internals as iint
import parser.eng_new as peng
import parser.ast_nodes as past
import utils.gen as ugen
import utils.consts as uconst
import utils.debug as udeb
import utils.err_codes as uerr

if ty.TYPE_CHECKING:
    import parser.internals as pint

TH_TokGrp = tuple[list[str], "pint.SpChr"]
TH_CmdFn = ty.Callable[[ugen.CmdData], int]
TH_GetCmdRes = tuple[TH_CmdFn, ugen.CmdSpec]


def fmt_t_ns(time_expo: int, ns: int) -> str | ty.NoReturn:
    """
    Format time in nanoseconds to required format.

    :param time_expo: Exponent to raise 10 to for dividing the time in
                      nanoseconds.
    :type time_expo: int

    :param ns: Time in nanoseconds.
    :type ns: int

    :returns: Formatted string.
    :rtype: str
    """
    if time_expo == 3:
        unit = "us"
    elif time_expo == 6:
        unit = "ms"
    elif time_expo == 0:
        unit = "ns"
    elif time_expo == 9:
        unit = "s"
    else:
        ugen.fatal(
            "Unrecognised debug time unit; this is not supposed to happen",
            uerr.ERR_UNK_ERR
        )

    return str(round(ns / 10 ** time_expo, 3)) + unit


class Intrpr:
    def __init__(
        self,
        cfg: cmgr.Cfg,
        pre_ld_ext_cmds: bool,
        stdout_ansi: bool,
        stderr_ansi: bool,
        debug_time_expo: int,
        log_lvl: int
    ) -> None:
        """
        Initialise the interpreter.

        :param cfg: Object containing configuration data.
        :type cfg: intrpr.cfg_mgr.Cfg

        :param pre_ld_ext_cmds: Load all external commands on interpreter
                                startup?
        :type pre_ld_ext_cmds: bool

        :param stdout_ansi: Keep ANSI escape codes in STDOUT redirects?
        :type stdout_ansi: bool

        :param stderr_ansi: Keep ANSI escape codes in STDERR redirects?
        :type stderr_ansi: bool

        :param debug_time_expo: Debug time division exponent
        :type debug_time_expo: int

        :param log_lvl: Log level for loggers
        :type log_lvl: int
        """
        self.ext_cached_cmds: dict[str, iint.CmdCacheEntry]

        # Interpreter initialisation time start
        _t_intrpr_init = time.perf_counter_ns()

        self.GET_CMD_ERR_MSG_MAP = {
            uerr.ERR_BAD_CMD: f"Bad command",
            uerr.ERR_NOT_VALID_CMD: f"No valid command file",
            uerr.ERR_NO_CMD_FN: f"No command function",
            uerr.ERR_NO_CMD_SPEC: f"Cannot find command spec",
            uerr.ERR_UNCALLABLE_CMD_FN: f"Uncallable command function",
            uerr.ERR_INV_NUM_PARAMS: f"Invalid number of command function parameters",
            uerr.ERR_MALFORMED_CMD_SPEC: f"Malformed command spec",
            uerr.ERR_RECUR_ERR: "Recursion depth exceeded; did you import the interpreter engine?",
            uerr.ERR_CMD_SYN_ERR: "Syntax error in command module",
            uerr.ERR_CANT_LD_CMD_MOD: "Cannot load command module"
        }

        ugen.warn_Q("Exercise caution when running untrusted commands")

        self.usr_dir = pl.Path("~").expanduser()
        self.uid = str(os.getuid())
        self.usernm = pwd.getpwuid(int(self.uid)).pw_name
        self.is_usr_root = (self.uid == "0")

        self.ext_cached_cmds = {}
        self.cfg = cfg
        self.stdout_ansi = stdout_ansi
        self.stderr_ansi = stderr_ansi
        self.debug_time_expo = debug_time_expo
        self.log_lvl = log_lvl
        self.env_vars = iint.Env()
        self.parser = peng.Parser()
        self.cmd_reslvr = icrsr.CmdReslvr(self.ext_cached_cmds,
                                          self.debug_time_expo)
        self._last_bad_prompt_obj = None

        self.env_vars.set("_USR_DIR_", str(self.usr_dir))
        self.env_vars.set("_PREV_CWD_", os.getcwd())
        self.env_vars.set("_LAST_RET_", uerr.ERR_ALL_GOOD)

        try:
            os.chdir(udeb.TMP_DIR)
        except FileNotFoundError:
            pass
        except PermissionError:
            pass
        except OSError:
            pass

        self.use_cfg()

        if pre_ld_ext_cmds:
            # DEBUG: Pre-load external modules time start
            _t_pre_ld = time.perf_counter_ns()
            self.ld_all_ext_mods()
            # DEBUG: Pre-load external module time end
            _t_pre_ld = time.perf_counter_ns() - _t_pre_ld
            ugen.debug_Q(
                ugen.fmt_d_stmt(
                    "time",
                    "tot_pre_ld_ext",
                    fmt_t_ns(self.debug_time_expo, _t_pre_ld)
                )
            )

        # Interpreter initialisation time end
        _t_intrpr_init = time.perf_counter_ns() - _t_intrpr_init

        ugen.debug_Q(
            ugen.fmt_d_stmt("time", "tot_init_intrpr",
                            fmt_t_ns(self.debug_time_expo, _t_intrpr_init))
        )

    def reslv_prompt_var(
        self,
        prompt: ty.Callable[[iint.Env], ty.Any] | str
    ) -> str:
        """
        "Resolve" the prompt variable. It can be function returning a string or
        a string.

        :param prompt: Prompt variable to "resolve."
        :type prompt: typing.Callable[[intrpr.internals.Env], typing.Any] | str

        :returns: Raw prompt string without prompt substitutions.
        :rtype: str
        """
        if isinstance(prompt, str):
            prompt_str = prompt

        elif callable(prompt):
            try:
                prompt_str = prompt(self.env_vars)
            except Exception as e:
                ugen.crit_Q(
                    f"Errant prompt function; raised {e.__class__.__name__} ({e})"
                )
                prompt_str = uconst.Defaults.PROMPT

            if not isinstance(prompt_str, str):
                ugen.crit_Q(
                    f"Expected return of type 'str' from prompt function; got '{type(prompt_str).__name__}'"
                )
                prompt_str = uconst.Defaults.PROMPT

        return prompt_str

    def reslv_prompt(
        self,
        prompt_obj: ty.Callable[[iint.Env], ty.Any] | str | None
    ) -> str:
        """
        "Resolve" the prompt, i.e. do all prompt substitutions.

        :param prompt_obj: Prompt string.
        :type prompt_obj: str
                          | typing.Callable[[intrpr.internals.Env], typing.Any]
                          | None

        :returns: Prompt string after prompt substitutions are performed.
        :rtype: str
        """
        # Pretty bad design, I guess, handling the None case for variable
        # prompt in this method, but I don't want to clutter up the main file
        if prompt_obj is None:
            prompt_obj = uconst.Defaults.PROMPT

        prompt = self.reslv_prompt_var(prompt_obj)
        len_prompt = len(prompt)
        final_prompt = ""
        skip = 0

        for i, char in enumerate(prompt):
            if skip:
                skip -= 1
                continue
            if char != "!":
                final_prompt += char
                continue
            # ! at the end of prompt
            if i == len_prompt - 1:
                # Issue warning only once
                if hash(self._last_bad_prompt_obj) != hash(prompt):
                    ugen.warn_Q(
                        "Lone '!' in prompt variable; falling back to default prompt",
                    )
                    self._last_bad_prompt_obj = prompt_obj
                return self.reslv_prompt(uconst.Defaults.PROMPT)

            nxt_chr = prompt[i + 1]

            # Condensed path
            if nxt_chr == "p":
                cwd_conden = re.sub(
                    f"^{re.escape(str(self.usr_dir))}",
                    "~",
                    os.getcwd()
                )
                final_prompt += cwd_conden
                skip += 1
                continue

            # Condensed path with slashes at the end for all directories except
            # the root and user directory
            elif nxt_chr == "P":
                cwd_conden = re.sub(
                    f"^{self.usr_dir}",
                    "~",
                    os.getcwd()
                )
                final_prompt += cwd_conden
                if not (cwd_conden == "~" or cwd_conden == "/"):
                    final_prompt += "/"
                skip += 1
                continue

            # Expanded path
            elif nxt_chr == "e":
                cwd = os.getcwd()
                final_prompt += cwd
                skip += 1
                continue

            # Username
            elif nxt_chr == "u":
                final_prompt += self.usernm
                skip += 1
                continue

            elif nxt_chr == "U":
                final_prompt += self.uid
                skip += 1
                continue

            # Hostname
            elif nxt_chr == "h":
                final_prompt += pf.node()
                skip += 1
                continue

            # Quark version
            elif nxt_chr == "v":
                final_prompt += uconst.VER
                skip += 1
                continue

            # Elevation symbols (how else can I describe this?)
            elif nxt_chr == "$":
                if self.is_usr_root:
                    final_prompt += "%"
                else:
                    final_prompt += "$"
                skip += 1
                continue

            elif nxt_chr == "?":
                final_prompt += str(self.env_vars.get("_LAST_RET_"))
                skip += 1
                continue

            # Literal '!'
            elif nxt_chr == "!":
                final_prompt += "!"
                skip += 1
                continue

            else:
                # Issue warning only once
                if hash(self._last_bad_prompt_obj) != hash(prompt_obj):
                    ugen.warn_Q(
                        f"Invalid prompt substitution symbol: '!{nxt_chr}'; falling back to default prompt"
                    )
                    self._last_bad_prompt_obj = prompt_obj
                return self.reslv_prompt(uconst.Defaults.PROMPT)

        return final_prompt

    def use_cfg(self) -> None:
        """
        Use user-provided config values, i.e. set interpreter attributes as per
        config given.
        """
        self.env_vars.set("_PROMPT_", self.cfg.prompt)
        expansion = {"@bin": uconst.BIN_PTH, "@prog": uconst.RUN_PTH}
        pths = []

        for pth in self.cfg.pth:
            if pth.startswith("@bin"):
                pth = re.sub("^@bin", uconst.BIN_PTH, pth)
            elif pth.startswith("@prog"):
                pth = re.sub("^@prog", uconst.RUN_PTH, pth)
            pths.append(str(pl.Path(pth).expanduser().absolute()))

        self.env_vars.set("_PTH_", tuple(pths))

    def ld_all_ext_mods(self) -> None:
        """
        Load all external modules into cache. Intended to be used at
        interpreter startup.
        """
        pths = self.env_vars.get("_PTH_")
        for pth in pths:
            pth = pl.Path(pth).expanduser().resolve()
            for i in os.scandir(pth):
                if os.path.isdir(i):
                    continue
                if not i.name.endswith(".py"):
                    continue
                if i.name == "__init__.py":
                    continue
                self.cmd_reslvr.ld_mod(
                    os.path.splitext(i.name)[0],
                    self.ext_cached_cmds,
                    pths
                )

    def get_cmd(
        self,
        cmd_nm: str,
        ext_cached_cmds: dict[str, iint.CmdCacheEntry],
        cmd_reslvr: icrsr.CmdReslvr,
        env_vars: iint.Env
    ) -> tuple[
        ty.Callable[[ugen.CmdData], int],
        ugen.CmdSpec,
        str
    ] | int:
        """
        Get the command function, command spec and command source using the
        command resolver.

        :param cmd_nm: Command name
        :type cmd_nm: str

        :param ext_cached_cmds: Cached external commands
        :type ext_cached_cmds: dict[str, intrpr.internals.CmdCacheEntry]

        :param cmd_reslvr: Command resolver object
        :type cmd_reslvr: intrpr.cmd_reslvr.CmdReslvr

        :param env_vars: Environment variables
        :type env_vars: intrpr.internals.Env

        :returns: If successful in fetching the command function and spec, a
                  tuple containing:
                      - the command function and
                      - the command spec.
                  Else, an integer error code.
        :rtype: tuple[
                    typing.Callable[[utils.gen.CmdData], int],
                    utils.gen.CmdSpec,
                    str
                ] | int
        """
        builtin_cmd = self.cmd_reslvr.get_builtin_cmd(cmd_nm)
        if isinstance(builtin_cmd, tuple):
            return (*builtin_cmd, "built-in")

        ext_cmd = self.cmd_reslvr.get_ext_cmd(
            cmd_nm,
            env_vars.get("_PTH_"),
            ext_cached_cmds
        )
        if isinstance(ext_cmd, int):
            return ext_cmd
        return (*ext_cmd, "external")

    def classi_params(
        self,
        params: "list[past.Param]",
        cmd_spec: ugen.CmdSpec
    ) -> tuple[tuple[str, ...], dict[str, str], tuple[str, ...]] | int:
        """
        Helper function to classify parser output into arguments, flags and
        options.

        :param tok_grp: Token group yielded from parser.
        :type tok_grp: list[parser.internals.Tok]

        :param cmd_spec: Command spec from command file.
        :type cmd_spec: utils.gen.CmdSpec

        :returns: If no errors occured, a tuple containing:
                      - a tuple of strings (argument array),
                      - a dictionary of string keys and string values (option
                        array) and
                      - a tuple of strings (flag array).
                  Otherwise, an integer error code.
        """
        args = []
        opts = {}
        flags = []
        arg_cnt = 0
        skip = 0

        # Iterate through the parser output
        for idx, param in enumerate(params[1 :]):
            param_val = param.val
            if skip:
                skip -= 1
                continue

            # LONG-FORM OPTIONS AND FLAGS
            if param_val.startswith("--") and not param.escd_hyphen:
                # Flags are given more preference
                if param_val in cmd_spec.flags:
                    flags.append(param_val)
                # Then options
                elif param_val in cmd_spec.opts:
                    if idx >= len(tok_grp) - 2:
                        ugen.err(f"Expected value for option '{param_val}'")
                        return uerr.ERR_EXPECTED_VAL_FOR_OPT
                    opts[param_val] = tok_grp[idx + 2].val
                    skip += 1
                # Invalid long-form option/flag
                else:
                    ugen.err(f"Invalid option/flag: '{param_val}'")
                    return uerr.ERR_INV_OPTS_FLAGS
                continue

            # SHORT-FORM OPTIONS AND FLAGS, OR COMBINED SHORT-FORM FLAGS
            if (
                param_val.startswith("-")
                and not param_val.startswith("--")
                and not param.escd_hyphen
            ):
                if param_val in cmd_spec.flags:
                    flags.append(param_val)
                elif param_val in cmd_spec.opts:
                    if idx >= len(tok_grp) - 2:
                        ugen.err(f"Expected value for option '{param_val}'")
                        return uerr.ERR_EXPECTED_VAL_FOR_OPT
                    opts[param_val] = tok_grp[idx + 2].val
                    skip += 1
                else:
                    # Lone '-'
                    if not param_val[1 :]:
                        ugen.err(f"Invalid option/flag: '{param_val}'")
                        return uerr.ERR_INV_OPTS_FLAGS
                    # Combined short flags
                    for i in param_val[1 :]:
                        if "-" + i in cmd_spec.flags:
                            flags.append("-" + i)
                            continue
                        ugen.err(f"Invalid option/flag: '{param_val}'")
                        return uerr.ERR_INV_OPTS_FLAGS
                continue

            # ARGUMENTS
            arg_cnt += 1
            if arg_cnt > cmd_spec.max_args:
                ugen.err(
                    f"Unexpected arguments; expected at most {cmd_spec.max_args}, got {arg_cnt}"
                )
                return uerr.ERR_UNEXPD_ARGS
            args.append(param_val)

        if arg_cnt < cmd_spec.min_args:
            ugen.err(
                f"Insufficient arguments; expected at least {cmd_spec.min_args}, got {arg_cnt}"
            )
            return uerr.ERR_INSUFF_ARGS

        return (tuple(args), opts, tuple(flags))

    def rd_from_fd(self, fd: io.IOBase, n: int) -> bytes:
        """
        Read data from stream.

        :param fd: Stream to read data from.
        :type fd: io.IOBase

        :param n: Number of bytes to read.
        :type n: int

        :returns: Bytes object read.
        :rtype: bytes
        """
        chunks = []
        total = 0

        while total < n:
            chunk = os.read(fd, n - total)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)

        return b"".join(chunks)

    def write_to_stream(
        self,
        txt: str | None,
        fl: "pint.Tok | None",
        typ: str
    ) -> int | ty.NoReturn:
        """
        :param txt: Text captured for redirection.
        :type txt: str | None

        :param fl: File to redirect stream to.
        :type fl: parser.internals.Tok | None

        :param typ: Type of redirection taking place (STDOUT/STDERR).
        :type typ: str

        :returns: Integer error code or program exit.
        :rtype: int | typing.NoReturn
        """
        if txt is None or fl is None:
            return uerr.ERR_ALL_GOOD
        if typ not in ("STDOUT", "STDERR"):
            ugen.fatal(
                f"Type of redirection was '{typ}', not supposed to happen",
                uerr.ERR_UNK_ERR
            )

        try:
            with open(fl.val, "w") as f:
                if not self.stdout_ansi and typ == "STDOUT":
                    f.write(ugen.rm_ansi("", txt))
                elif not self.stderr_ansi and typ == "STDERR":
                    f.write(ugen.rm_ansi("", txt))
                else:
                    f.write(txt)
        except PermissionError:
            ugen.err_Q(f"Access denied; cannot write STDERR to file \"{fl.val}\"")
            return uerr.ERR_PERM_DENIED
        except FileNotFoundError:
            ugen.err_Q(f"Empty file; cannot write STDERR to file \"{fl.val}\"")
            return uerr.ERR_EMPTY_FL_REDIR
        except Exception as e:
            ugen.fatal_Q(
                f"Unknown error ({e}); cannot write STDERR to file \"{fl.val}\"",
                uerr.ERR_UNK_FATAL,
                tb.format_exc()
            )
            return uerr.ERR_UNK_ERR

    def loop_set_lgr_streams(
        self,
        chk_if: io.TextIOBase,
        set_to: io.TextIOBase
    ) -> None:
        """
        Loop through and set logger streams.

        :param chk_if: Object to check if streams against
        :type chk_if: io.TextIOBase

        :param set_to: Object to set streams to
        :type set_to: io.TextIOBase
        """
        for lgr in lg.Logger.manager.loggerDict.values():
            if isinstance(lgr, lg.PlaceHolder):
                continue
            for hdlr in lgr.handlers:
                if hdlr.stream is chk_if:
                    hdlr.stream = set_to

    def cmd_resln(self, cmd_nm: str) -> iint.CmdReslnRes | int:
        # DEBUG: Command resolution time start
        _t_cmd_resln = time.perf_counter_ns()

        err_code = uerr.ERR_ALL_GOOD
        get_cmd_res = self.get_cmd(
            cmd_nm,
            self.ext_cached_cmds,
            self.cmd_reslvr,
            self.env_vars
        )

        if isinstance(get_cmd_res, int):
            # Write error message to current STDERR
            err_msg = self.GET_CMD_ERR_MSG_MAP.get(
                get_cmd_res,
                "missing_err_msg"
            )
            err_code = get_cmd_res
            ugen.err_Q(f"{err_msg}: '{cmd_nm}'")
            return get_cmd_res

        # DEBUG: Command resolution time end
        _t_cmd_resln = time.perf_counter_ns() - _t_cmd_resln
        ugen.debug_Q(
            ugen.fmt_d_stmt(
                "time",
                "cmd_reslv",
                fmt_t_ns(self.debug_time_expo, _t_cmd_resln)
            )
        )

        return iint.CmdReslnRes(*get_cmd_res)

    def hdl_op_redir(
        self,
        par_out: tuple[TH_TokGrp],
        tok_grp: TH_TokGrp,
        idx: int,
        old_stream: io.TextIOBase,
        buf_stream: io.StringIO,
        typ: str
    ) -> tuple[TH_TokGrp, int, str] | int | ty.NoReturn:
        """
        Handle the STDOUT/STDERR redirection operation.

        :param par_out: Whole output from the parser for the whole input line.
        :type par_out: tuple[TH_TokGrp]

        :param tok_grp: Current token group (one element of par_out).
        :type tok_grp: TH_TokGrp

        :param idx: Index of current token group in whole parser output.
        :type idx: int

        :param old_stream: Original stream.
        :type old_stderr: io.TextIOBase

        :param buf_stream: Created stream.
        :type buf_stderr: io.StringIO

        :param typ: Type of redirection (STDOUT/STDERR).
        :type typ: str

        :returns: If no errors were encountered, a tuple containing:
                      - the patched token group,
                      - the number of token groups to skip next and
                      - the redirect output filename.
                  Else, an integer error code.
        :rtype: tuple[TH_TokGrp, int, str] | int
        """
        # CURSED
        try:
            nxt_grp, sp_chr = par_out[idx + 1]
            redir_fl = nxt_grp[0]
        except IndexError:
            ugen.err_Q("Missing filename for STDERR redirection")
            return uerr.ERR_MISSING_FL_REDIR

        # Add the next token group to the current token group, excluding the
        # STDERR redirect filename
        tok_grp.extend(nxt_grp[1 :])
        skip_grp = 1

        if typ == "STDERR":
            sys.stderr = buf_stream
        elif typ == "STDOUT":
            sys.stdout = buf_stream
        else:
            ugen.fatal(
                "Stream redirection type was '{typ}'. Not supposed to happen",
                uerr.ERR_UNK_ERR
            )

        # Loop through handlers and set their streams to the buffer created
        # only if STDERR is being redirected
        if typ == "STDERR":
            self.loop_set_lgr_streams(old_stream, buf_stream)
        return (tok_grp, skip_grp, redir_fl)

    def child_proc(
        self,
        cmd_fn: TH_CmdFn,
        data: ugen.CmdData,
        w: int
    ) -> ty.NoReturn:
        """
        Helper function to handle the child process execution for external
        commands.

        :param cmd_fn: Command function to execute.
        :type cmd_fn: TH_CmdFn

        :param data: Command data to be passed to command function call.
        :type data: utils.gen.CmdData

        :param w: Write pipe descriptor.
        :type w: int

        :param old_stdout: Original STDOUT stream.
        :type old_stdout: io.TextIOBase

        :param buf_stdout: Stream to capture STDOUT.
        :type buf_stdout: io.StringIO

        :returns: - (os._exit).
        :rtype: typing.NoReturn
        """
        tmp_buf = io.StringIO()
        stdout_bkup = sys.stdout
        sys.stdout = tmp_buf
        try:
            cmd_ret = self.rn_cmd_fn(cmd_fn, data)
        finally:
            sys.stdout = stdout_bkup

        if type(cmd_ret) != int:
            ugen.crit("Last command returned non-integer")
            cmd_ret = uerr.ERR_CMD_RETD_NON_INT
        elif not (-2 ** 31 <= cmd_ret < 2 ** 31):
            ugen.crit("Command return value exceeds 32-bit integer limit")
            cmd_ret = uerr.ERR_RET_INT_TOO_LARGE

        out_sz = tmp_buf.tell()
        out = tmp_buf.getvalue()
        # Pass output size and output through the pipe to parent process
        os.write(w, st.pack("!iQ", cmd_ret, out_sz))
        os.write(w, out.encode())
        os._exit(cmd_ret)

    def exec_cmd(self, cmd_nm: str, params: list[past.Param], is_tty: bool, stdin: str):
        # Resolve command
        cmd_resln_res = self.cmd_resln(cmd_nm)
        if isinstance(cmd_resln_res, int):
            return cmd_resln_res
        cmd_fn = cmd_resln_res.cmd_fn
        cmd_spec = cmd_resln_res.cmd_spec
        cmd_src = cmd_resln_res.cmd_src
        # Classify parameters into arguments, options and flags
        tmp = self.classi_params(params, cmd_spec)
        if isinstance(tmp, int):
            return tmp
        args, opts, flags = tmp

        data = ugen.CmdData(
            cmd_nm=cmd_nm,
            args=tuple(args),
            opts=opts,
            flags=tuple(flags),
            cmd_reslvr=self.cmd_reslvr,
            env_vars=self.env_vars,
            ext_cached_cmds=self.ext_cached_cmds,
            term_sz=os.get_terminal_size(),
            is_tty=is_tty,
            stdin=stdin,
            exec_fn=iint.exec_fn_dummy,
            operation=""                        # Dummy as of now
        )
        return self.exec_cmd_fn(cmd_fn=cmd_fn, cmd_src=cmd_src, data=data)

    def exec_cmd_fn(
        self,
        cmd_fn: TH_CmdFn,
        cmd_src: str,
        data: ugen.CmdData
    ) -> iint.CmdCompdObj:
        err_code = uerr.ERR_ALL_GOOD

        if cmd_src == "external":
            r, w = os.pipe()
            pid = os.fork()
            # Child process, run in a forked process
            if pid == 0:
                os.close(r)
                self.child_proc(cmd_fn, data, w)
            # Some issue, can't fork
            elif pid < 0:
                ugen.crit_Q(
                    "Failed to fork current process; try re-running the command"
                )
                err_code = err_code or uerr.ERR_CANT_FORK_PROC
            # Parent process
            else:
                # Do NOT rely on the child process's exit code! It could be
                # incorrect because the OS only recognises 8-bit integers for
                # exit codes
                os.close(w)
                # 4 bytes for command return code
                # 8 bytes for output length
                # "Output length" bytes for output
                ret_packed = self.rd_from_fd(r, 4)
                ret_code = st.unpack("!i", ret_packed)[0]
                out_sz_packed = self.rd_from_fd(r, 8)
                out_sz = st.unpack("!Q", out_sz_packed)[0]
                out = self.rd_from_fd(r, out_sz).decode()
                os.close(r)
                # This should prevent zombie (defunct) processes
                _, status = os.wait()
                exit_status = os.WEXITSTATUS(status)
                err_code = err_code or ret_code

        # Built-in command, run in same process as the interpreter
        elif cmd_src == "built-in":
            tmp_buf = io.StringIO()
            stdout_bkup = sys.stdout
            sys.stdout = tmp_buf
            try:
                cmd_ret = self.rn_cmd_fn(cmd_fn, data)
            finally:
                sys.stdout = stdout_bkup
            out = tmp_buf.getvalue()
            err_code = err_code or cmd_ret

        else:
            raise LogicalErr(f"Invalid command source string: '{cmd_src}'")

        return iint.CmdCompdObj(stdout=out, err_code=err_code)

    def is_syn_ok(self, cmd_expr: past.CmdExpr) -> int:
        num_ops = len(cmd_expr.ops)
        i = 0

        while i < num_ops:
            l_simp_cmd = cmd_expr.get_simp_cmd(i)
            r_simp_cmd = cmd_expr.get_simp_cmd(i + 1)
            op = cmd_expr.get_op(i)

            # No parameters on the right of operator
            if r_simp_cmd is None:
                ugen.err_Q(
                    f"Expected at least one parameter on the right of operator at pos {op.end}"
                )
                return uerr.ERR_EXPD_PARAM_RT_OP
            # Too many parameters on the right of STDOUT redirect operator
            if isinstance(op, past.RedirSTDOUT) and len(r_simp_cmd) > 1:
                ugen.err_Q(
                    f"Unexpected parameter for STDOUT redirection at pos {cmd_expr.r_opr.params[1].start}"
                )
                return uerr.ERR_UNEXPD_PARAM_STDOUT_REDIRN
            # Too many parameters on the right of STDERR redirect operator
            elif isinstance(op, past.RedirSTDERR) and len(r_simp_cmd) > 1:
                ugen.err_Q(
                    f"Unexpected parameter for STDERR redirection at pos {cmd_expr.r_opr.params[1].start}"
                )
                return uerr.ERR_UNEXPD_PARAM_STDOUT_REDIRN

            i += 1

    def rn_cmd_fn(
        self,
        cmd_fn: TH_CmdFn,
        data: ugen.CmdData
    ) -> int:
        """
        Run a command function.

        :param cmd_fn: Command function to execute.
        :type cmd_fn: TH_CmdFn

        :param data: Data to be passed to the command function.
        :type data: utils.gen.CmdData

        :returns: Integer error code.
        :rtype: int
        """
        cmd_ret = uerr.ERR_ALL_GOOD

        try:
            cmd_ret = cmd_fn(data)
        # Variable type mismatch
        except ugen.InvVarTypErr as e:
            cmd_ret = cmd_ret or uerr.ERR_ENV_VAR_INV_TYP
            ugen.err_Q(
                f"Invalid variable type for '{e.var_nm}'; expected '{e.var_typ.__name__}', got '{e.got_typ.__name__}'"
            )
        # Invalid variable name
        except ugen.InvVarNmErr as e:
            cmd_ret = cmd_ret or uerr.ERR_ENV_VAR_INV_NM
            ugen.err_Q(f"Invalid variable name: '{e.var_nm}'")
        # Unknown variable
        except ugen.UnkVarErr as e:
            cmd_ret = cmd_ret or uerr.ERR_ENV_UNK_VAR
            ugen.err_Q(f"Unknown variable: '{e.var_nm}'")
        # Other exceptions raised
        except Exception as e:
            cmd_ret = cmd_ret or uerr.ERR_CMD_RNTIME_ERR
            ugen.crit_Q(f"Errant command: '{data.cmd_nm}'")
            ugen.crit_Q(f"Raised {e.__class__.__name__}")
            ugen.crit_Q(f"Message: {e}")
            ugen.crit_Q(tb.format_exc())

        return cmd_ret

    def exec_cmd_expr(
        self,
        cmd_expr: past.CmdExpr,
        stdin: str
    ):
        syn_ok = self.is_syn_ok(cmd_expr)
        if syn_ok:
            return syn_ok

        err_code = uerr.ERR_ALL_GOOD
        skip = 0
        # Empty command
        if not cmd_expr.simp_cmds:
            # TODO: Change this later to some other code, if needed, and then
            # handle it in the calling function
            return uerr.ERR_ALL_GOOD

        for i, simp_cmd in enumerate(cmd_expr):
            if skip:
                skip -= 1
                continue

            old_stdout = sys.stdout
            old_stderr = sys.stderr

            op = cmd_expr.get_op(i)
            params = simp_cmd.params
            is_tty = True
            is_pipe = isinstance(op, past.Pipe)
            is_redir_stdout = isinstance(op, past.RedirSTDOUT)
            is_redir_stderr = isinstance(op, past.RedirSTDERR)
            if is_pipe or is_redir_stdout or is_redir_stderr:
                is_tty = False

            # Pipe
            if is_pipe:
                buf_stdout = io.StringIO()
                sys.stdout = buf_stdout

            # Redirect STDOUT
            elif is_redir_stdout:
                redir_flnm = cmd_expr[i + 1][0]
                try:
                    stdout_fl = open(redir_flnm, "w")
                except IsADirectoryError:
                    ugen.err_Q(f"Is a directory: \"{redir_flnm}\"")
                except PermissionError:
                    ugen.err_Q(
                        f"Access denied; cannot redirect STDOUT to \"{redir_flnm}\""
                    )
                    return uerr.ERR_PERM_DENIED
                except OSError as e:
                    # TODO: Change the error code later
                    ugen.err_Q(
                        f"OS error: cannot redirect STDOUT to \"{redir_flnm}\"; {e.strerror}"
                    )
                    return uerr.ERR_OS_ERR
                sys.stdout = stdout_fl
                skip += 1

            # Redirect STDERR
            elif is_redir_stderr:
                redir_flnm = cmd_expr[i + 1][0]
                try:
                    stderr_fl = open(redir_flnm, "w")
                except IsADirectoryError:
                    ugen.err_Q(f"Is a directory: \"{redir_flnm}\"")
                except PermissionError:
                    ugen.err_Q(
                        f"Access denied; cannot redirect STDERR to \"{redir_flnm}\""
                    )
                    return uerr.ERR_PERM_DENIED
                except OSError as e:
                    # TODO: Change the error code later
                    ugen.err_Q(
                        f"OS error: cannot redirect STDERR to \"{redir_flnm}\"; {e.strerror}"
                    )
                    return uerr.ERR_OS_ERR
                sys.stderr = stderr_fl
                skip += 1

            try:
                cmd_nm = params.pop(0).val
                res = self.exec_cmd(
                    cmd_nm,
                    params,
                    is_tty=is_tty,
                    stdin=stdin
                )
                err_code = err_code or res.err_code
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            if is_pipe:
                stdin = buf_stdout.read()

        return err_code

    def exec_cmd_seq(self, cmd_seq: past.CmdSeq):
        err_code = uerr.ERR_ALL_GOOD
        for cmd_expr in cmd_seq:
            err_code = self.exec_cmd_expr(cmd_expr, stdin="")
        return err_code

    def exec(self, ln: str):
        tmp = self.parser.get_cmd_seq(ln, start=0)
        if isinstance(tmp, int):
            return tmp
        return self.exec_cmd_seq(tmp)
