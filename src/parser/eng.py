#
# Provides the parser for the interpreter.
#

import typing as ty

import parser.internals as pint
import utils.err_codes as uerr
import utils.consts as uconst
import utils.gen as ugen
import utils.debug as udeb


class Parser:
    def __init__(self) -> None:
        pass

    def _get_sp_chr(self, ln: str, start: int) -> pint.SpChr | None:
        if ln[start] in uconst.SP_CHRS:
            return pint.SpChr(val=ln[start], start=start, end=start + 1)
        return None

    def _get_unquoted_tok(self, ln: str, start: int) -> pint.Tok:
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
            if ch in uconst.SP_CHRS and ln[idx - 1] != "\\":
                break
            idx += 1

        return pint.Tok(
            val=ln[start : idx],
            quoted=False,
            quote_typ=None,
            start=start,
            end=idx
        )

    def _get_quoted_tok(self, ln: str, start: int, quote: str) \
            -> pint.Tok | int:
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
            ugen.err_Q(f"No closing quote at position {idx}")
            return uerr.ERR_NO_CLOSING_QUOTE

        return pint.Tok(
            # Do not include the closin quote in the value
            ln[elem_start : idx - 1],
            quoted=True,
            quote_typ=quote,
            start=start,
            end=idx
        )

    def _get_nxt_tok(
        self,
        ln: str,
        start: int
    ) -> pint.Tok | pint.SpChr | int | None:
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
        tok: pint.Tok | pint.SpChr | int | None

        # Encountered whitespace
        if ln[start].isspace():
            return None

        if ln[start] in pint.QUOTES:
            tok = self._get_quoted_tok(ln, start, ln[start])
        elif ln[start] in uconst.SP_CHRS:
            tok = self._get_sp_chr(ln, start)
        else:
            tok = self._get_unquoted_tok(ln, start)

        if isinstance(tok, int):
            return tok

        return tok

    def _reslv_esc_chrs(
        self,
        tok: pint.Tok | pint.SpChr
    ) -> pint.Tok | pint.SpChr | int:
        """
        "Resolve" escape characters in tokens lexed. Resolution in this context
        means escaped characters in the source string to escape characters
        (like "\\n" to "\n").

        :param tok: The token to "resolve" escape characters in.
        :type tok: parser.internals.Tok | parser.internals.SpChr

        :returns: The "resolved" token or error code.
        :rtype: parser.internals.Tok | parser.internals.SpChr | int
        """
        reslvd_tok_val = []
        tok_val_len = len(tok.val)
        skip = 0
        escd_hyphen = False

        if isinstance(tok, pint.SpChr):
            return tok

        for i, char in enumerate(tok.val):
            if skip:
                skip -= 1
                continue

            if char != "\\":
                reslvd_tok_val.append(char)
                continue
            if i == tok_val_len - 1:
                ugen.err_Q(f"Lone backslash at position {tok.start + i}")
                return uerr.ERR_LONE_B_SLASH

            tmp = pint.ESC_CHR_MAP.get("\\" + tok.val[i + 1])
            if tmp is None:
                reslvd_tok_val.append(tok.val[i + 1])
            else:
                reslvd_tok_val.append(tmp)
            skip += 1

            if not i and tok.val[i + 1] == "-":
                escd_hyphen = True

        return pint.Tok(
            val="".join(reslvd_tok_val),
            quoted=tok.quoted,
            quote_typ=tok.quote_typ,
            start=tok.start,
            end=tok.end,
            escd_hyphen=escd_hyphen
        )

    def lex(self, ln: str) -> list[pint.Tok | pint.SpChr] | int:
        idx = 0
        ln_len = len(ln)
        tok_list = []
        tok_list_reslvd = []

        while idx < len(ln):
            tok = self._get_nxt_tok(ln, idx)
            # Encountered whitespace
            if tok is None:
                idx += 1
                continue
            # Encountered errors
            elif isinstance(tok, int):
                return tok

            tok_list.append(tok)
            idx += tok.end - tok.start

        for tok in tok_list:
            reslvd_tok = self._reslv_esc_chrs(tok)
            if isinstance(reslvd_tok, int):
                return reslvd_tok
            tok_list_reslvd.append(reslvd_tok)

        return tok_list_reslvd
