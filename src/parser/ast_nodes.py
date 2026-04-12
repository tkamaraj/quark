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
class Cmd:
    pass


@dc.dataclass(repr=False)
class SimpCmd(Cmd):
    params: list[Param]

    def __repr__(self) -> str:
        return f"{self.params}"


@dc.dataclass(repr=False)
class BinCmd(Cmd):
    op: Op
    l_opr: Cmd
    r_opr: Cmd

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} -> {self.l_opr} {self.op} {self.r_opr}"


@dc.dataclass(repr=False)
class Sequence:
    cmds: list[Cmd]
