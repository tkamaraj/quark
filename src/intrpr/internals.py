import importlib.machinery as ilm
import typing as ty
import types

import src.utils.err_codes as uerr
import src.utils.gen as ugen

if ty.TYPE_CHECKING:
    import src.intrpr.cmd_reslvr as icrsr


# To not lose the traceback string (note that I said string) during the
# pickling process; stores the traceback as a string in an attribute, as the
# __traceback__ attribute of the exceptions gets dropped during pickling
class ExcepWNoLoss:
    def __init__(self, e: Exception) -> None:
        self.e = e
        self.exc_txt = tb.format_tb(self.e.__traceback__)


class CmdCompdObj(ty.NamedTuple):
    err_code: int


class CmdCacheEntry(ty.NamedTuple):
    cmd: str
    spec: ilm.ModuleSpec
    mod: types.ModuleType
    sz: int
    mtime: float


class CmdReslnRes(ty.NamedTuple):
    cmd_fn: ty.Callable[[ugen.CmdData], int]
    cmd_spec: ugen.CmdSpec
    cmd_src: str


class EnvVar:
    def __init__(self, nm: str, val: ty.Any, protected: bool = False) -> None:
        self.nm = nm
        self._val = val
        self.typ = type(val)
        self.protected = protected

        # Invalid identifier
        if nm.lower().strip("_abcdefghijklmnopqrstuvwxyz0123456789") \
                or nm.startswith("0123456789"):
            raise ugen.InvVarNmErr(var_nm=nm)

    def _chk_correct_typ(self, val: ty.Any) -> bool:
        if not isinstance(val, self.typ):
            return False
        return True

    @property
    def val(self) -> ty.Any:
        return self._val

    @val.setter
    def val(self, value: ty.Any) -> int:
        # if not isinstance(value, self.typ):
        #     raise ugen.InvVarTypErr(
        #         var_nm=self.nm,
        #         var_typ=self.typ,
        #         got_typ=type(value)
        #     )
        self._val = value
        return uerr.ERR_ALL_GOOD

    def __repr__(self) -> str:
        return rf"nm={self.nm} val={repr(self.val)} typ={self.typ.__name__}"

    def __str__(self) -> str:
        return self.__repr__()


class Env:
    def __init__(self):
        self.env_vars: dict[str, EnvVar]
        self.env_vars = {}

    def set(self, nm: str, val: ty.Any) -> None | ty.NoReturn:
        var_obj = self.env_vars.get(nm)
        # New variable
        if var_obj is None:
            self.env_vars[nm] = EnvVar(nm, val)
        else:
            self.env_vars[nm].val = val

    def get(self, nm: str) -> ty.Any | ty.NoReturn:
        var_obj = self.env_vars.get(nm)
        if var_obj is None:
            raise ugen.UnkVarErr(var_nm=nm)
        return var_obj.val

    def rm(self, nm: str) -> None:
        try:
            self.env_vars.pop(nm)
        except KeyError as e:
            pass

    def __iter__(self) -> ty.Generator[EnvVar, None, None]:
        for i in self.env_vars.values():
            yield i

    def __contains__(self, val: ty.Any) -> bool:
        return val in self.env_vars

    def __repr__(self) -> str:
        return str(self.env_vars)


def exec_fn_dummy(*args, **kwargs) -> None:
    pass
