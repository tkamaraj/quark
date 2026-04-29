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
import select as sel
import struct as st
import sys
import time
import traceback as tb
import typing as ty

import intrpr.cfg_mgr as cmgr
import intrpr.cmd_reslvr as icrsr
import intrpr.internals as iint
import parser.eng as peng
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
            uerr.ERR_BAD_CMD: "Bad command",
            uerr.ERR_INV_CMD: "Invalid command file",
            uerr.ERR_NO_CMD_FN: "Missing command function",
            uerr.ERR_NO_CMD_SPEC: "Missing command spec",
            uerr.ERR_NO_HELP_OBJ: "Missing help object",
            uerr.ERR_UNCALLABLE_CMD_FN: "Uncallable command function",
            uerr.ERR_INV_NUM_PARAMS: "Bad function argument count",
            uerr.ERR_INV_CMD_SPEC: "Bad command spec",
            uerr.ERR_INV_HELP_OBJ: "Bad help oject",
            uerr.ERR_RECUR_ERR: "Recursion limit exceeded",
            uerr.ERR_CMD_SYN_ERR: "Syntax error",
            uerr.ERR_CANT_LD_CMD_MOD: "Load failed"
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
        self.env_vars.set("_ALIASES_", self.cfg.aliases)
        # expansions = {"@bin": uconst.BIN_PTH, "@prog": uconst.RUN_PTH}
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
        params_len = len(params)

        # Iterate through the parser output
        for idx, param in enumerate(params):
            param_val = param.val
            if skip:
                skip -= 1
                continue

            # LONG-FORM OPTIONS AND FLAGS
            if param_val.startswith("--") and not param.escd_hyp:
                # Flags are given more preference
                if param_val in cmd_spec.flags:
                    flags.append(param_val)
                # Then options
                elif param_val in cmd_spec.opts:
                    if idx >= params_len - 1:
                        ugen.err(f"Expected value for option '{param_val}'")
                        return uerr.ERR_EXPD_VAL_OPT
                    opts[param_val] = params[idx + 1].val
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
                and not param.escd_hyp
            ):
                if param_val in cmd_spec.flags:
                    flags.append(param_val)
                elif param_val in cmd_spec.opts:
                    if idx >= params_len - 1:
                        ugen.err(f"Expected value for option '{param_val}'")
                        return uerr.ERR_EXPD_VAL_OPT
                    opts[param_val] = params[idx + 1].val
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
            aliases = self.env_vars.get("_ALIASES_")
            if cmd_nm in aliases:
                get_cmd_res = self.get_cmd(
                    aliases[cmd_nm],
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

    def child_proc(
        self,
        cmd_fn: TH_CmdFn,
        data: ugen.CmdData,
        w1: int,
        w2: int
    ) -> ty.NoReturn:
        os.dup2(w1, 1)
        os.close(w1)
        cmd_ret = self.rn_cmd_fn(cmd_fn, data)
        if not isinstance(cmd_ret, int):
            ugen.crit("Last command returned non-integer")
            cmd_ret = uerr.ERR_CMD_RETD_NON_INT
        elif not (-2 ** 31 <= cmd_ret < 2 ** 31):
            ugen.crit_Q(
                f"Command return value exceeds 32-bit signed integer limit: {cmd_ret}"
            )
            cmd_ret = uerr.ERR_RET_INT_TOO_LARGE
        # Pass output size and output through the pipe to parent process
        os.write(w2, st.pack("!i", cmd_ret))
        os.close(w2)
        os._exit(cmd_ret)

    def exec_cmd_fn(
        self,
        cmd_fn: TH_CmdFn,
        cmd_src: str,
        data: ugen.CmdData,
        stdout_obj: io.TextIOBase,
        stderr_obj: io.TextIOBase
    ) -> iint.CmdCompdObj:
        err_code = uerr.ERR_ALL_GOOD

        pid = None
        try:
            if cmd_src == "external":
                ugen.debug("resolved to external command")
                # Two pipes, 1 and 2, for command output and return code
                r1, w1 = os.pipe()
                r2, w2 = os.pipe()
                pid = os.fork()

                # Child process, run in a forked process
                if pid == 0:
                    os.close(r1)
                    os.close(r2)
                    self.child_proc(cmd_fn, data, w1, w2)
                # Some issue, can't fork
                elif pid < 0:
                    ugen.crit_Q(
                        "Failed to fork current process; try re-running the command"
                    )
                    err_code = err_code or uerr.ERR_CANT_FORK_PROC
                # Parent process
                else:
                    # Do NOT rely on child process exit codes, because OS only
                    # supports 8-bit unsigned integers
                    os.close(w1)
                    os.close(w2)
                    # For obtaining output as it's pushed through pipe 1 from the
                    # child process
                    poller = sel.poll()
                    poller.register(r1)
                    done = False
                    while not done:
                        evts = poller.poll()
                        for fd, evt in evts:
                            # Event when pipe closes
                            if evt & sel.POLLHUP:
                                done = True
                            # Event when pipe has data
                            if evt & sel.POLLIN:
                                chunk = os.read(r1, 4096)
                                if not chunk:
                                    break
                                stdout_obj.write(chunk.decode())
                    # 4 bytes for command return code in pipe 2
                    ret_packed = self.rd_from_fd(r2, 4)
                    ret_code = st.unpack("!i", ret_packed)[0]
                    os.close(r2)
                    # To prevent zombie (defunct) processes
                    _, status = os.wait()
                    exit_status = os.WEXITSTATUS(status)
                    err_code = err_code or ret_code

            # Built-in command, run in same process as the interpreter
            elif cmd_src == "built-in":
                ugen.debug("resolved to built-in command")
                cmd_ret = self.rn_cmd_fn(cmd_fn, data)
                err_code = err_code or cmd_ret

            else:
                raise LogicalErr(f"Invalid command source string: '{cmd_src}'")

        except KeyboardInterrupt as e:
            if pid != 0:
                raise ugen.KeyboardInterruptWPrevileges(str(e), child_pid=pid)
            else:
                raise e

        return iint.CmdCompdObj(err_code=err_code)

    def exec_cmd(
        self,
        cmd_nm: str,
        cmd_fn: TH_CmdFn,
        cmd_spec: ugen.CmdSpec,
        cmd_src: str,
        params: list[past.Param],
        is_tty: bool,
        stdin: str,
        stdout_obj: io.TextIOBase,
        stderr_obj: io.TextIOBase
    ):
        # Classify parameters into arguments, options and flags
        tmp = self.classi_params(params, cmd_spec)
        if isinstance(tmp, int):
            return iint.CmdCompdObj(tmp)
        args, opts, flags = tmp

        try:
            term_sz = os.get_terminal_size()
        except OSError:
            term_sz = None
        data = ugen.CmdData(
            cmd_nm=cmd_nm,
            args=tuple(args),
            opts=opts,
            flags=tuple(flags),
            cmd_reslvr=self.cmd_reslvr,
            env_vars=self.env_vars,
            ext_cached_cmds=self.ext_cached_cmds,
            term_sz=term_sz,
            is_tty=is_tty,
            stdin=stdin,
            exec_fn=self.exec,
            operation=""                        # Dummy as of now
        )
        return self.exec_cmd_fn(cmd_fn, cmd_src, data, stdout_obj, stderr_obj)

    def exec_cmd_expr(
        self,
        cmd_expr: past.CmdExpr,
        stdin: str
    ):
        # DEBUG: Expression execute time start
        _t_exec_expr = time.perf_counter_ns()

        syn_ok = self.is_syn_ok(cmd_expr)
        if syn_ok:
            return syn_ok

        err_code = uerr.ERR_ALL_GOOD
        skip = 0
        # Empty command, and cmd_expr will ALWAYS have one SimpCmd object in
        # simp_cmds list, even if the input line was empty
        if not cmd_expr.simp_cmds[0].params:
            return self.env_vars.get("_LAST_RET_")

        ugen.debug(
            ugen.fmt_d_stmt(
                "gen",
                "exec expr",
                cmd_expr
            )
        )

        for i, simp_cmd in enumerate(cmd_expr):
            if skip:
                skip -= 1
                continue

            op = cmd_expr.get_op(i)
            params = simp_cmd.params
            # Resolve command
            cmd_nm = params.pop(0).val
            cmd_resln_res = self.cmd_resln(cmd_nm)
            if isinstance(cmd_resln_res, int):
                return cmd_resln_res
            cmd_fn = cmd_resln_res.cmd_fn
            cmd_spec = cmd_resln_res.cmd_spec
            cmd_src = cmd_resln_res.cmd_src

            is_tty = True
            is_pipe = isinstance(op, past.Pipe)
            is_redir_stdout = isinstance(op, past.RedirSTDOUT)
            is_redir_stderr = isinstance(op, past.RedirSTDERR)
            stdout_obj = sys.stdout
            stderr_obj = sys.stderr

            if is_pipe or is_redir_stdout or is_redir_stderr:
                is_tty = False

            # Pipe
            if is_pipe:
                buf_stdout = io.StringIO()
                stdout_obj = buf_stdout

            # Redirect STDOUT
            elif is_redir_stdout:
                # get_simp_cmd can be called without worry because the syntax
                # is guaranteed to be ok, checked by is_syn_ok at the start of
                # this method. So, there shall be atleast one element in
                # parameter list of the SimpCmd objects
                redir_param = cmd_expr.get_simp_cmd(i + 1).get_param(0)
                redir_flnm = redir_param.val
                err_msg_head = "redirect STDOUT failed;"
                try:
                    stdout_fl = open(redir_flnm, "w")
                except IsADirectoryError:
                    ugen.err_Q(
                        f"{err_msg_head} is a directory: \"{redir_flnm}\" (pos {redir_param.start})"
                    )
                    return uerr.ERR_IS_A_DIR
                except PermissionError:
                    ugen.err_Q(
                        f"{err_msg_head} access denied: \"{redir_flnm}\""
                    )
                    return uerr.ERR_PERM_DENIED
                except OSError as e:
                    # TODO: Change the error code later
                    ugen.err_Q(f"{err_msg_head} OS error; {e.strerror}")
                    return uerr.ERR_OS_ERR
                stdout_obj = stdout_fl
                skip += 1

            # Redirect STDERR
            elif is_redir_stderr:
                redir_flnm = cmd_expr.get_simp_cmd(i + 1).get_param(0)
                err_msg_head = "redirect STDERR failed;"
                try:
                    stderr_fl = open(redir_flnm.val, "w")
                except IsADirectoryError:
                    ugen.err_Q(f"{err_msg_head} is a directory: \"{redir_flnm}\"")
                    return uerr.ERR_IS_A_DIR
                except PermissionError:
                    ugen.err_Q(
                        f"{err_msg_head} access denied: \"{redir_flnm}\""
                    )
                    return uerr.ERR_PERM_DENIED
                except OSError as e:
                    ugen.err_Q(
                        f"{err_msg_head} OS error; {e.strerror}"
                    )
                    return uerr.ERR_OS_ERR
                stderr_obj = stderr_fl
                self.loop_set_lgr_streams(sys.stderr, stderr_obj)
                skip += 1

            # I don't know what the problem is, but I have to do this to make
            # piping work for expressions involving built-in commands
            if is_pipe and cmd_src == "built-in":
                old_stdout = sys.stdout
                sys.stdout = buf_stdout

            try:
                res = self.exec_cmd(
                    cmd_nm,
                    cmd_fn,
                    cmd_spec,
                    cmd_src,
                    params,
                    is_tty,
                    stdin,
                    stdout_obj,
                    stderr_obj
                )
                err_code = err_code or res.err_code
            finally:
                # Undo changes made for piping involving built-in commands
                if is_pipe and cmd_src == "built-in":
                    sys.stdout = old_stdout
                if is_redir_stderr:
                    self.loop_set_lgr_streams(stderr_obj, sys.stderr)

            stdin = ""
            if is_pipe:
                stdin = buf_stdout.getvalue()
                ugen.debug(
                    ugen.fmt_d_stmt(
                        "gen",
                        f"STDIN from '{cmd_nm}'",
                        f"{len(stdin)} chrs"
                    )
                )

        # DEBUG: Expression execute time end
        ugen.debug_Q(
            ugen.fmt_d_stmt(
                "time",
                "expr_exec",
                fmt_t_ns(
                    self.debug_time_expo,
                    time.perf_counter_ns() - _t_exec_expr
                )
            )
        )
        return err_code

    def exec_cmd_seq(self, cmd_seq: past.CmdSeq):
        err_code = uerr.ERR_ALL_GOOD
        # DEBUG: Full sequence execute time start
        _t_full_seq = time.perf_counter_ns()

        for cmd_expr in cmd_seq:
            err_code = self.exec_cmd_expr(cmd_expr, stdin="")

        # DEBUG: Full sequence execute time end
        ugen.debug_Q(
            ugen.fmt_d_stmt(
                "time",
                "full_seq_exec",
                fmt_t_ns(
                    self.debug_time_expo,
                    time.perf_counter_ns() - _t_full_seq
                )
            )
        )
        return err_code

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
            if len(r_simp_cmd) < 1:
                ugen.err_Q(
                    f"Missing parameter for operator '{op}' at pos {op.end}"
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

        return uerr.ERR_ALL_GOOD

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

        # DEBUG: Run command function time start
        _t_rn_cmd_fn = time.perf_counter_ns()

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
            ugen.crit_Q(
                f"Uncaught exception in command '{data.cmd_nm}': {e.__class__.__name__}"
            )
            ugen.lg_to_fl("c", tb.format_exc())

        # DEBUG: Run command function time end
        ugen.debug(
            ugen.fmt_d_stmt(
                "time",
                "rn_cmd_fn",
                fmt_t_ns(
                    self.debug_time_expo,
                    time.perf_counter_ns() - _t_rn_cmd_fn
                )
            )
        )
        return cmd_ret

    def exec(self, ln: str):
        tmp = self.parser.get_cmd_seq(ln, os.getcwd(), start=0)
        if isinstance(tmp, int):
            return tmp
        return self.exec_cmd_seq(tmp)
