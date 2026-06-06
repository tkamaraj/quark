import atexit
import collections.abc as cabc
import copy
import ctypes as ct
import dataclasses as dcs
import importlib.machinery as ilm
import multiprocessing as mp
import multiprocessing.shared_memory as mpshm
import struct as st
import time
import traceback as tb
import typing as ty
import types

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


@dcs.dataclass
class EnvTbl:
    shm: mpshm.SharedMemory = dcs.field(init=False)
    cnt: int = dcs.field(init=False)

    def __post_init__(self) -> None:
        # self.cnt is the number of items in the table
        self.SHM_SZ = 512 * 1024        # 512 KiB
        self.shm = mpshm.SharedMemory(
            create=True,
            track=True,
            size=self.SHM_SZ
        )
        self.cnt = 0
        self.wrt_idx = 0
        self.lock = mp.Lock()
        atexit.register(self.shm.unlink)

    def __len__(self) -> int:
        return self.cnt

    def __iter__(self) -> ty.NoReturn:
        raise NotImplementedError(
            f"__iter__ not implemented yet for {self.__class__.__name__}"
        )

    def __contains__(self, key: ty.Any) -> bool:
        raise NotImplementedError(
            f"__contains__ not implemented yet for {self.__class__.__name__}"
        )

    def __getitem__(self, key: str) -> ty.Any | ty.NoReturn:
        if self.shm.buf is None:
            raise RuntimeError("Operation of closed shared memory descriptor")
        off = 0
        for _ in range(self.cnt):
            len_key, len_val = st.unpack("!QQ", self.shm.buf[off : off + 16])
            off += 16
            cur_key = self.shm.buf[off : off + len_key].tobytes().decode()
            off += len_key
            # Not the key we're looking for...
            if cur_key != key:
                off += len_val
                continue
            # Found the motherfucker!
            return self.shm.buf[off : off + len_val].tobytes().decode()
        raise ugen.UnkVarErr(var_nm=key)

    def __setitem__(self, key: str, val: str) -> None | ty.NoReturn:
        len_key: ct.c_uint64
        len_val: ct.c_uint64

        if self.shm.buf is None:
            raise RuntimeError("Operation of closed shared memory descriptor")
        # Validate key and val are strings
        if not isinstance(key, str):
            raise ugen.InvVarNmErr(var_nm=key)
        if not isinstance(val, str):
            raise ugen.InvVarValErr(var_nm=key, var_val=val)
        # Structure in memory:
        # .++++++++++++++++,
        # |   key length   | -> 8B
        # | -------------- |
        # |  value length  | -> 8B
        # | -------------- |
        # |      key       | -> (key length)B
        # | -------------- |
        # |     value      | -> (value length)B
        # `++++++++++++++++'
        tmp_len_key = len(key)
        tmp_len_val = len(val)
        # Check bounds for key and values (stored as 8-byte ints)
        if not ((0 <= tmp_len_key < 2 ** 64) and (0 <= tmp_len_val < 2 ** 64)):
            raise MemoryError("Items too large")
        # I'm having this here, just in case, so that any metadata (if any)
        # from the int object does not mess with me
        len_key = ct.c_uint64(tmp_len_key)
        len_val = ct.c_uint64(tmp_len_val)
        bytes_reqd = 8 + 8 + len_key.value + len_val.value
        if self.wrt_idx >= self.SHM_SZ - bytes_reqd:
            raise MemoryError("Insufficient memory")

        # Acquire lock and write to shared memory
        with self.lock:
            len_data = st.pack(
                "!QQ",
                len_key.value,
                len_val.value
            )
            self.shm.buf[self.wrt_idx : self.wrt_idx + 16] = len_data                   # Length of key and value
            self.wrt_idx += 16
            self.shm.buf[self.wrt_idx : self.wrt_idx + len_key.value] = key.encode()    # Key itself
            self.wrt_idx += len_key.value
            self.shm.buf[self.wrt_idx : self.wrt_idx + len_val.value] = val.encode()    # Value itself
            self.wrt_idx += len_val.value
            self.cnt += 1

        return None

    def __repr__(self) -> str:
        raise NotImplementedError("__repr__ not implemented yet")

    def set(self, nm: str, val: ty.Any) -> None | ty.NoReturn:
        return self.__setitem__(nm, val)

    def get(self, nm: str) -> ty.Any | ty.NoReturn:
        return self.__getitem__(nm)

    def rm(self, nm: str) -> None:
        raise NotImplementedError("Implement rm")

    def items(self) -> cabc.ItemsView[str, ty.Any]:
        raise NotImplementedError("Implement items")


@dcs.dataclass
class IntrprTbl:
    intrpr_tbl: dict[str, ty.Any] = dcs.field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.intrpr_tbl)

    def __iter__(self) -> ty.NoReturn:
        raise NotImplementedError("__iter__ not implemented yet")

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

    def set(self, nm: str, val: ty.Any) -> None | ty.NoReturn:
        return self.__setitem__(nm, val)

    def get(self, nm: str) -> ty.Any | ty.NoReturn:
        return self.__getitem__(nm)

    def rm(self, nm: str) -> None:
        try:
            self.intrpr_tbl.pop(nm)
        except KeyError as e:
            pass

    def items(self) -> cabc.ItemsView[str, ty.Any]:
        return self.intrpr_tbl.items()

    def crt_self_cp(self) -> ty.Self:
        return copy.deepcopy(self)
