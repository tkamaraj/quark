import typing as ty

import parser.ast_nodes as past
import parser.internals as pint
import utils.err_codes as uerr
import utils.consts as uconst
import utils.gen as ugen
import utils.debug as udeb


class Parser:
    def __init__(self) -> None:
        self.LOGI_OP_CHR_NODE_MAP = {
            "&": past.And,
            "^": past.Or
        }
        self.DATA_OP_CHR_NODE_MAP = {
            "|": past.Pipe,
            ">": past.RedirSTDOUT,
            "?": past.RedirSTDERR
        }

    def _get_unquoted_tok(self, ln: str, start: int) -> past.Param:
        """
        Get an unquoted token from the source line.

        :param ln: The source line to lex.
        :type ln: str

        :param start: The index to start lexing from in the source.
        :type start: int

        :returns: A token object.
        :rtype: parser.internals.Tok
        """
        idx = start

        for ch in ln[start :]:
            if ch.isspace():
                break
            if ch in pint.QUOTES and ln[idx - 1] != "\\":
                break
            if ch in (*pint.LOGI_OPS, *pint.DATA_OPS, *pint.CMD_SEPRS) and ln[idx - 1] != "\\":
                break
            idx += 1

        return past.Unquoted(
            val=ln[start : idx],
            escd_hyp=False,       # False for now, this will be updated
            start=start,
            end=idx
        )

    def _get_quoted_tok(
        self,
        ln: str,
        start: int,
        quote: str
    ) -> past.Quoted | int:
        """
        Get a quoted token from the source line.

        :param ln: The source line to lex.
        :type ln: str
        :param start: The index to start lexing from in the source.
        :type start: int

        :param quote: The "quote" character to match to end the quoted token.
        :type quote: str

        :returns: A token object or error code.
        :rtype: parser.internals.Tok | int
        """
        # Exclude the opening quote from the index
        elem_start = idx = start + 1
        prev_chr = None

        for char in ln[elem_start :]:
            # Before the if statement to include the closing quote in the index
            idx += 1
            if char == quote and prev_chr != "\\":
                break
            prev_chr = char
        else:
            ugen.err_Q(f"No closing quote at position {idx}\n")
            return uerr.ERR_NO_CLOSING_QUOTE

        return past.Quoted(
            # Do not include the closin quote in the value
            ln[elem_start : idx - 1],
            escd_hyp=False,
            quote=quote,
            start=start,
            end=idx
        )

    def _get_nxt_param(
        self,
        ln: str,
        start: int
    ) -> past.Tok | past.Op | None | int:
        """
        Get the next token from the source line.

        :param ln: The source line to lex.
        :type ln: str

        :param start: The index to start lexing from in the source.
        :type start: int

        :returns: A token object, special character object, error code or
                  NoneType object.
        :rtype: parser.internals.Tok | parser.internals.SpChr | int | None
        """
        param: past.Param | past.Op | int | None

        # Encountered whitespace
        idx = start
        idx = self._skip_ws(ln, idx)

        if ln[idx] in pint.QUOTES:
            param = self._get_quoted_tok(ln, idx, ln[idx])
        elif ln[idx] in (*pint.LOGI_OPS, *pint.DATA_OPS):
            return None
        elif ln[idx] in pint.CMD_SEPRS:
            return None
        else:
            param = self._get_unquoted_tok(ln, idx)

        if isinstance(param, int):
            return param

        return self._reslv_esc_chrs(param)

    def _reslv_esc_chrs(
        self,
        param: past.Param | past.Op
    ) -> past.Param | past.SpChr | int:
        """
        "Resolve" escape characters in tokens lexed. Resolution in this context
        means escaped characters in the source string to escape characters
        (like "\\n" to "\n").

        :param tok: The token to "resolve" escape characters in.
        :type tok: parser.internals.Tok | parser.internals.SpChr

        :returns: The "resolved" token or error code.
        :rtype: parser.internals.Tok | parser.internals.SpChr | int
        """
        reslvd_val = []
        param_len = len(param.val)
        skip = 0
        escd_hyp = False

        if isinstance(param, past.Op):
            return param

        for i, char in enumerate(param.val):
            if skip:
                skip -= 1
                continue

            if char != "\\":
                reslvd_val.append(char)
                continue
            if i == param_len - 1:
                ugen.err_Q(f"Lone backslash at position {param.start + i}\n")
                return uerr.ERR_LONE_B_SLASH

            tmp = pint.ESC_CHR_MAP.get("\\" + param.val[i + 1])
            if tmp is None:
                reslvd_val.append(param.val[i + 1])
            else:
                reslvd_val.append(tmp)
            skip += 1

            if not i and param.val[i + 1] == "-":
                escd_hyp = True

        # Unquoted
        if param.__class__ == past.Unquoted:
            return past.Unquoted(
                val="".join(reslvd_val),
                escd_hyp=escd_hyp,
                start=param.start,
                end=param.end,
            )
        # Quoted, unless I'm very mistaken
        else:
            return past.Quoted(
                val="".join(reslvd_val),
                quote=param.quote,
                escd_hyp=escd_hyp,
                start=param.start,
                end=param.end,
            )

    def _get_simp_cmd(self, ln: str, start: int) -> past.SimpCmd | int:
        ln_len = len(ln)
        idx = start
        params = []
        while idx < ln_len:
            idx = self._skip_ws(ln, idx)
            nxt_param = self._get_nxt_param(ln, idx)
            if isinstance(nxt_param, int):
                return nxt_param
            # When the next parameter is not related to SimpCmd, e.g. an
            # operator or a command separator
            if nxt_param is None:
                break
            idx = nxt_param.end
            params.append(nxt_param)
        return past.SimpCmd(params)

    def _get_cmd_expr(
        self,
        ln: str,
        start: int
    ) -> tuple[list[past.SimpCmd], list[past.Op], int] | int:
        ln_len = len(ln)
        simp_cmds = []
        ops = []

        # Get the first operand
        simp_cmd = self._get_simp_cmd(ln, start)
        if isinstance(simp_cmd, int):
            return simp_cmd
        simp_cmds.append(simp_cmd)
        idx = simp_cmd.params[-1].end if simp_cmd.params else start

        while idx < ln_len:
            # Get the operator
            idx = self._skip_ws(ln, idx)
            curr_ch = ln[idx]
            if curr_ch in pint.LOGI_OPS:
                op = self.LOGI_OP_CHR_NODE_MAP[curr_ch](
                    val=curr_ch,
                    start=idx,
                    end=idx + 1
                )
            elif curr_ch in pint.DATA_OPS:
                op = self.DATA_OP_CHR_NODE_MAP[curr_ch](
                    val=curr_ch,
                    start=idx,
                    end=idx + 1
                )
            else:
                return (simp_cmds, ops, idx)

            ops.append(op)
            # For the operator character
            idx += 1

            # Get each subsequent operand
            idx = self._skip_ws(ln, idx)
            simp_cmd = self._get_simp_cmd(ln, idx)
            if isinstance(simp_cmd, int):
                return simp_cmd
            simp_cmds.append(simp_cmd)
            idx = simp_cmd.params[-1].end if simp_cmd.params else idx

        return (simp_cmds, ops, idx)

    def _grp_cmd_expr(
        self,
        simp_cmds: list[past.SimpCmd],
        ops: list[past.Op]
    ) -> tuple[list[BinCmd], int]:
        ops_len = len(ops)
        grped = simp_cmds[0]

        for idx, curr_op in enumerate(ops):
            opr = simp_cmds[idx + 1]
            grped = past.BinCmd(op=curr_op, l_opr=grped, r_opr=opr)

        return grped

    def get_cmd_seq(self, ln: str, start: int = 0):
        ln_len = len(ln)
        idx = start
        cmd_exprs = []

        idx = self._skip_ws(ln, idx)
        res = self._get_cmd_expr(ln, start)
        if isinstance(res, int):
            return cmd_exprs
        simp_cmds, ops, idx = res
        cmd_exprs.append(self._grp_cmd_expr(simp_cmds, ops))

        while idx < ln_len:
            idx = self._skip_ws(ln, idx)
            curr_ch = ln[idx]
            if curr_ch not in pint.CMD_SEPRS:
                return uerr.ERR_UNRECOGD_CMD_SEPR

            # For the command separator character
            idx += 1

            idx = self._skip_ws(ln, idx)
            res = self._get_cmd_expr(ln, idx)
            if isinstance(res, int):
                return cmd_exprs
            simp_cmds, ops, idx = res
            cmd_exprs.append(self._grp_cmd_expr(simp_cmds, ops))

        return cmd_exprs

    def _skip_ws(self, ln: str, idx: int) -> int:
        ln_len = len(ln)
        while idx < ln_len and ln[idx].isspace():
            idx += 1
        return idx

    def test(self, ln: str, start: idx) -> None:
        udeb.pprn(self._get_cmd_seq(ln, start))
