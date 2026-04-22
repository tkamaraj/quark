import dataclasses as dc


@dc.dataclass(repr=False)
class Tok:
    val: str
    start: str
    end: str

    def __repr__(self) -> str:
        return repr(self.val)

    def __str__(self) -> str:
        return self.__repr__()


@dc.dataclass(repr=False)
class Op(Tok):
    pass


@dc.dataclass(repr=False)
class Param(Tok):
    escd_hyp: bool


@dc.dataclass(repr=False)
class DataOp(Op):
    def __repr__(self) -> str:
        return self.val


@dc.dataclass(repr=False)
class Pipe(DataOp):
    pass


@dc.dataclass(repr=False)
class RedirSTDOUT(DataOp):
    pass


@dc.dataclass(repr=False)
class RedirSTDERR(DataOp):
    pass


@dc.dataclass(repr=False)
class LogOp(Op):
    pass


@dc.dataclass(repr=False)
class And(LogOp):
    pass


@dc.dataclass(repr=False)
class Or(LogOp):
    pass


@dc.dataclass(repr=False)
class Unquoted(Param):
    pass


@dc.dataclass(repr=False)
class Quoted(Param):
    quote: str


@dc.dataclass(repr=False)
class SimpCmd:
    params: list[Param]

    def __repr__(self) -> str:
        return f"{self.params}"


@dc.dataclass(repr=False)
class CmdExpr:
    simp_cmds: list[SimpCmd]
    ops: list[Op]

    def get_op(self, idx: int) -> Op | None:
        if idx >= len(self.ops):
            return None
        return self.ops[idx]

    def get_simp_cmd(self, idx: int) -> SimpCmd | None:
        if idx >= len(self.simp_cmds):
            return None
        return self.simp_cmds[idx]

    def __repr__(self) -> str:
        return f"{self.simp_cmds}"

    def __iter__(self) -> ty.Generator[SimpCmd, None, None]:
        for i in self.simp_cmds:
            yield i

    def __len__(self) -> int:
        return len(self.simp_cmds)


@dc.dataclass(repr=False)
class CmdSeq:
    cmds: list[CmdExpr]

    def __repr__(self) -> str:
        return f"{self.cmds}"

    def __iter__(self) -> ty.Generator[CmdExpr, None, None]:
        for i in self.cmds:
            yield i
