import collections.abc as cabc
import copy
import ctypes as ct
import dataclasses as dcs
import functools
import importlib.machinery as ilm
import struct as st
import threading as th
import traceback as tb
import typing as ty
import types
if ty.TYPE_CHECKING:
    import multiprocessing as mp
    import multiprocessing.shared_memory as mpshm

import utils.err_codes as uerr
import utils.gen as ugen
if ty.TYPE_CHECKING:
    import intrpr.cmd_reslvr as icrsr


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
    pth: str
    fl_hash: int
    sz: int
    mtime: float


class CmdReslnRes(ty.NamedTuple):
    cmd_fn: ty.Callable[[ugen.CmdData], int]
    cmd_spec: ugen.CmdSpec
    cmd_src: str


class Snoo:
    def __init__(self) -> None:
        self.CMD_SPEC = ugen.CmdSpec(
            min_args=0,
            max_args=float("inf"),
            opts=(),
            flags=("-C", "--no-crash"),
            parse_sub_cmds=False
        )
        self.HELP = ugen.HelpObj(
            usage="snoo [flag] [...]",
            summary="Oh, you'll see...",
            details=(
                "ARGUMENTS",
                ("none", ""),
                "OPTIONS",
                ("none", ""),
                "FLAGS",
                ("-C, --no-crash", "Do not crash the interpreter")
            )
        )

    def run(self, data: ugen.CmdData) -> int | ty.NoReturn:
        crash = True
        for flag in data.flags:
            if flag in ("-C", "--no-crash"):
                crash = False
        if crash:
            ugen.fatal_Q("Beauty overload", ret=uerr.ERR_MP_BEAUTY_OVERLD)
        else:
            ugen.crit_Q("Beauty overload")
            return uerr.ERR_BEAUTY_OVERLD


def catch_exceps_env_tbl(
    f: ty.Callable[[ty.Any, ...], ty.Any]
) -> ty.Callable[[ty.Any, ...], ty.Any] | ty.NoReturn:
    @functools.wraps(f)
    def fn(*args, **kwargs) -> ty.Any | ty.NoReturn:
        try:
            return f(*args, **kwargs)
        except st.error:
            ugen.fatal_Q("Corrupted shared memory; cannot continue execution")
    return fn


@dcs.dataclass
class EnvTbl:
    """
    Structure in memory:
     .++++++++++++++,
     |    count     |  --> 8B
     |--------------|
     | write index  |  --> 8B
     `--------------'
    .++++++++++++++++,            --,
    ||  key length  || --> 8B       |
    ||--------------||              |
    || value length || --> 8B       |
    ||--------------||              | ---> 8192B (8KiB) per entry
    ||     key      || --> 128B     |
    ||--------------||              |
    ||    value     || --> 8048B    |
    `++++++++++++++++'            --'
    """
    shm: "mpshm.SharedMemory"
    lock: "mp.Lock"

    def __post_init__(self) -> None:
        self.SHM_SZ = self.shm.size
        self.CNT_SZ = 8                                                         # Size to store number of items
        self.WRT_IDX_SZ = 64                                                    # Size to store write index
        self.KEY_LEN_SZ = 8                                                     # Size to store key length
        self.VAL_LEN_SZ = 8                                                     # Size to store value length
        self.KEY_MAX_SZ = 128                                                   # Maximum allowed size of key
        self.VAL_MAX_SZ = 8048                                                  # Maximum allowed size of value
        self.ENTRY_BYTES_REQD = (                                               # Size required for each entry
            self.KEY_LEN_SZ
            + self.VAL_LEN_SZ
            + self.KEY_MAX_SZ
            + self.VAL_MAX_SZ
        )
        self.LEN_DATA_SZ = self.KEY_LEN_SZ + self.VAL_LEN_SZ                    # Size of key and value length combined
        self.CNT_START = 0                                                      # Start offset of number of items
        self.WRT_IDX_START = self.CNT_SZ                                        # Start offset of write index
        self.ENTRY_START = self.CNT_SZ + self.WRT_IDX_START                     # Start offset of entries
        self.wrt_cnt(0)                                                         # Set count, i.e. number of items to 0
        self.wrt_wrt_idx(self.ENTRY_START)                                      # Set write index to start of entries

    def __bool__(self) -> bool:
        return bool(self.get_cnt())

    def __len__(self) -> int:
        return self.get_cnt()

    def __iter__(self) -> ty.Iterable[tuple[str, str]]:
        cnt = self.get_cnt()
        off = self.ENTRY_START
        for _ in range(cnt):
            len_key, len_val = st.unpack("!QQ", self.shm.buf[off : off + 16])
            off += 16
            cur_key = self.shm.buf[off : off + len_key].tobytes().decode()
            off += self.KEY_MAX_SZ
            cur_val = self.shm.buf[off : off + len_val].tobytes().decode()
            off += self.VAL_MAX_SZ
            yield (cur_key, cur_val)

    def __contains__(self, key: ty.Any) -> bool:
        try:
            self.get(key)
            return True
        except ugen.UnkVarErr:
            return False

    def __getitem__(self, key: str) -> ty.Any | ty.NoReturn:
        return self.get(key)

    def __setitem__(self, key: str, val: str) -> None | ty.NoReturn:
        return self.set(key, val)

    @catch_exceps_env_tbl
    def __repr__(self) -> str:
        data_dict = {}
        for pair in self:
            data_dict[pair[0]] = pair[1]
        return str(data_dict)

    @catch_exceps_env_tbl
    def get_cnt(self) -> int | ty.NoReturn:
        return st.unpack(
            "!Q",
            self.shm.buf[self.CNT_START : self.WRT_IDX_START]
        )[0]

    def wrt_cnt(self, cnt: int) -> None | ty.NoReturn:
        if not (0 <= cnt <= 2 ** self.CNT_SZ - 1):
            raise ugen.EnvCntOutOfRng()
        with self.lock:
            self.shm.buf[: self.WRT_IDX_START] = st.pack("!Q", cnt)
        return None

    @catch_exceps_env_tbl
    def get_wrt_idx(self) -> int | ty.NoReturn:
        return st.unpack(
            "!Q",
            self.shm.buf[self.WRT_IDX_START : self.ENTRY_START]
        )[0]

    def wrt_wrt_idx(self, wrt_idx: int) -> None | ty.NoReturn:
        if not (0 <= wrt_idx < 2 ** self.WRT_IDX_SZ):
            raise ugen.EnvWrtIdxOutOfRng()
        with self.lock:
            self.shm.buf[self.WRT_IDX_START : self.ENTRY_START] = st.pack(
                "!Q",
                wrt_idx
            )
        return None

    def set(self, key: str, val: str) -> None | ty.NoReturn:
        if self.shm.buf is None:
            raise RuntimeError("Operation of closed shared memory descriptor")
        # Validate key and val are strings
        if not isinstance(key, str):
            raise ugen.InvVarNmErr(var_nm=key)
        if not isinstance(val, str):
            raise ugen.InvVarValErr(var_nm=key, var_val=val)

        # Validate data received (key and value)
        encoded_key = key.encode()
        encoded_val = val.encode()
        len_key = len(encoded_key)
        len_val = len(encoded_val)
        # Check if length of key and value is more than allowed
        if len_key > self.KEY_MAX_SZ:
            raise ugen.EnvKeyTooLarge(f"Key too large: '{key}' ({len_key})")
        if len_val > self.VAL_MAX_SZ:
            prn_val = val[: 10] + "..." if len(val) > 10 else val
            raise ugen.EnvValTooLarge(f"Value length too large: '{prn_val}' ({len_val})")
        # Check bounds for key and value lengths (stored as 8-byte ints)
        # Not needed, but let it be there, just in case
        if not ((0 <= len_key < 2 ** 64) and (0 <= len_val < 2 ** 64)):
            raise ugen.EnvKeyValLenOverflow("Item(s) too large")

        # See if key already exists, in which case it needs to be just updated
        cnt = len(self)
        wrt_idx = self.get_wrt_idx()
        end_wrt_idx = wrt_idx
        prev_entry_present = False
        for (nm, val) in self:
            if key == nm:
                # 128 subtracted for the key's assigned memory
                # 16 (8 + 8) subtracted for the key and value's lengths' assigned memory
                # Because we need the start of the entry, which is at the start of the key length's memory
                wrt_idx = self.get(key, ret_off=True) - 128 - 16
                prev_entry_present = True
        if wrt_idx >= self.SHM_SZ - self.ENTRY_BYTES_REQD:
            raise MemoryError(
                f"Shared memory exhausted; need {self.ENTRY_BYTES_REQD}B, available {self.SHM_SZ - self.ENTRY_BYTES_REQD}B"
            )

        ugen.debug_Q(
            ugen.fmt_d_stmt(
                "env",
                f"write index for current entry (thread {th.current_thread().name})",
                str(wrt_idx),
                lhs_rhs_sep=": "
            )
        )
        ugen.debug_Q(
            ugen.fmt_d_stmt(
                "env",
                f"previous entry present",
                str(prev_entry_present),
                lhs_rhs_sep=": "
            )
        )
        # Acquire lock and write to shared memory
        with self.lock:
            len_data = st.pack("!QQ", len_key, len_val)
            self.shm.buf[wrt_idx : wrt_idx + self.LEN_DATA_SZ] = len_data       # Length of key and value
            wrt_idx += self.LEN_DATA_SZ
            self.shm.buf[wrt_idx : wrt_idx + len_key] = encoded_key             # Key itself
            wrt_idx += self.KEY_MAX_SZ
            self.shm.buf[wrt_idx : wrt_idx + len_val] = encoded_val             # Value itself
            wrt_idx += self.VAL_MAX_SZ
            self.wrt_cnt(cnt + 1) if not prev_entry_present else None
            self.wrt_wrt_idx(end_wrt_idx + self.ENTRY_BYTES_REQD) if not prev_entry_present else None
        ugen.debug_Q(
             ugen.fmt_d_stmt(
                 "env",
                 "after env table write",
                 f"count = {self.get_cnt()}, write index = {self.get_wrt_idx()}",
                 lhs_rhs_sep=": "
             )
        )
        ugen.debug_Q("[env] after write: ")

        return None

    @catch_exceps_env_tbl
    def get(self, key: str, ret_off: bool = False) -> str | ty.NoReturn:
        if self.shm.buf is None:
            raise RuntimeError("Operation of closed shared memory descriptor")

        cnt = len(self)
        for off in range(self.ENTRY_START, self.SHM_SZ, 8192):
            len_key, len_val = st.unpack(
                "!QQ",
                self.shm.buf[off : off + self.LEN_DATA_SZ]
            )
            off += self.LEN_DATA_SZ
            cur_key = self.shm.buf[off : off + len_key].tobytes().decode()
            off += self.KEY_MAX_SZ
            # Not the key we're looking for...
            if cur_key != key:
                off += self.VAL_MAX_SZ
                continue
            # Found the motherfucker!
            return (
                off
                if ret_off else
                self.shm.buf[off : off + len_val].tobytes().decode()
            )
        raise ugen.UnkVarErr(var_nm=key)

    def rm(self, nm: str) -> None:
        raise NotImplementedError("Implement rm")


@dcs.dataclass
class IntrprTbl:
    intrpr_tbl: dict[str, ty.Any] = dcs.field(default_factory=dict)
    protection_status: dict[str, bool] = dcs.field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.intrpr_tbl)

    def __iter__(self) -> ty.NoReturn:
        yield from self.intrpr_tbl

    def __contains__(self, key: ty.Any) -> bool:
        return key in self.intrpr_tbl

    def __getitem__(self, key: str) -> ty.Any | ty.NoReturn:
        if key not in self.intrpr_tbl:
            raise ugen.UnkVarErr(var_nm=key)
        return self.intrpr_tbl[key]

    def __setitem__(self, key: str, val: ty.Any) -> None:
        if key not in self.intrpr_tbl:
            if (
                key.lower().strip("_abcdefghijklmnopqrstuvwxyz0123456789")
                or key.startswith("0123456789")
            ):
                raise ugen.InvVarNmErr(var_nm=key)
        self.intrpr_tbl[key] = val
        return None

    def __repr__(self) -> str:
        return str(self.intrpr_tbl)

    def set(
        self,
        nm: str,
        val: ty.Any,
        protected: bool = False
    ) -> None | ty.NoReturn:
        tmp = self.__setitem__(nm, val)
        self.protection_status[nm] = protected
        return tmp

    def get(self, nm: str) -> ty.Any | ty.NoReturn:
        return self.__getitem__(nm)

    def pop(self, nm: str) -> None:
        try:
            # If protected, raise InvAccess
            if self.protection_status[nm]:
                raise ugen.InvAccess(f"Pop of protected variable: {nm}")
            self.intrpr_tbl.pop(nm)
        except KeyError:
            pass

    def items(self) -> cabc.ItemsView[str, ty.Any]:
        return self.intrpr_tbl.items()

    def crt_self_cp(self) -> ty.Self:
        return copy.deepcopy(self)
