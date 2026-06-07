import collections.abc as cabc
import copy
import ctypes as ct
import dataclasses as dcs
import importlib.machinery as ilm
import multiprocessing as mp
import struct as st
import multiprocessing.shared_memory as mpshm
import traceback as tb
import typing as ty
import types

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
    shm: mpshm.SharedMemory

    def __post_init__(self) -> None:
        self.SHM_SZ = self.shm.size
        self.CNT_START_IDX = 0
        self.WRT_IDX_START_IDX = 8
        self.ENTRY_START_IDX = 16
        self.wrt_cnt(self.CNT_START_IDX)
        self.wrt_wrt_idx(self.ENTRY_START_IDX)
        self.lock = mp.Lock()

    def __len__(self) -> int:
        return st.unpack(
            "!Q",
            self.shm.buf[self.CNT_START_IDX : self.WRT_IDX_START_IDX]
        )[0]

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
        cnt = len(self)
        off = self.ENTRY_START_IDX
        for _ in range(cnt):
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

    def get_key_idx_in_mem(self, key: str) -> int | None:
        # INCOMPLETE!
        cnt = self.get_cnt()
        off = self.ENTRY_START_IDX
        for _ in range(cnt):
            len_key, len_val = st.unpack(self.shm.buf[off : off + 16])[0]
            off += 16
            cur_key = self.shm.buf[off : off + len_key].tobytes().decode()
            if cur_key == key:
                return offset
            # WE WILL NEED TO SHIFT THE OTHER ENTRIES IF WE PROCEED WITH THIS
            # APPROACH!

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
        # ||  key length  || -> 8B
        # ||--------------||
        # || value length || -> 8B
        # ||--------------||
        # ||     key      || -> (key length)B
        # ||--------------||
        # ||    value     || -> (value length)B
        # `++++++++++++++++'
        cnt = len(self)
        wrt_idx = self.get_wrt_idx()
        tmp_len_key = len(key.encode())
        tmp_len_val = len(val.encode())
        # Check bounds for key and values (stored as 8-byte ints)
        if not ((0 <= tmp_len_key < 2 ** 64) and (0 <= tmp_len_val < 2 ** 64)):
            raise MemoryError("Item(s) too large")
        # I'm having this here, just in case, so that any metadata (if any)
        # from the int object does not mess with me
        len_key = ct.c_uint64(tmp_len_key)
        len_val = ct.c_uint64(tmp_len_val)
        bytes_reqd = 8 + 8 + len_key.value + len_val.value
        if wrt_idx >= self.SHM_SZ - bytes_reqd:
            raise MemoryError("Insufficient memory")

        # Acquire lock and write to shared memory
        with self.lock:
            len_data = st.pack(
                "!QQ",
                len_key.value,
                len_val.value
            )
            self.shm.buf[wrt_idx : wrt_idx + 16] = len_data                 # Length of key and value
            wrt_idx += 16
            self.shm.buf[wrt_idx : wrt_idx + len_key.value] = key.encode()  # Key itself
            wrt_idx += len_key.value
            self.shm.buf[wrt_idx : wrt_idx + len_val.value] = val.encode()  # Value itself
            wrt_idx += len_val.value
            self.wrt_cnt(cnt + 1)
            self.wrt_wrt_idx(wrt_idx)

        return None

    def __repr__(self) -> str:
        cnt = self.get_cnt()
        off = self.ENTRY_START_IDX
        data_dict = {}
        for _ in range(cnt):
            len_key, len_val = st.unpack("!QQ", self.shm.buf[off : off + 16])
            off += 16
            cur_key = self.shm.buf[off : off + len_key].tobytes().decode()
            off += len_key
            cur_val = self.shm.buf[off : off + len_val].tobytes().decode()
            off += len_val
            data_dict[cur_key] = cur_val
        return str(data_dict)

    def get_cnt(self) -> int | ty.NoReturn:
        return self.__len__()

    def wrt_cnt(self, cnt: int) -> None | ty.NoReturn:
        c_cnt = ct.c_int64(cnt)
        self.shm.buf[: self.WRT_IDX_START_IDX] = st.pack("!Q", c_cnt.value)
        return None

    def get_wrt_idx(self) -> int | ty.NoReturn:
        return st.unpack(
            "!Q",
            self.shm.buf[self.WRT_IDX_START_IDX : self.ENTRY_START_IDX]
        )[0]

    def wrt_wrt_idx(self, wrt_idx: int) -> None | ty.NoReturn:
        c_wrt_idx = ct.c_int64(wrt_idx)
        self.shm.buf[self.WRT_IDX_START_IDX : self.ENTRY_START_IDX ] = st.pack(
            "!Q",
            c_wrt_idx.value
        )
        return None

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
