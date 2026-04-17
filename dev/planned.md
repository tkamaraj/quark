# PLANNED

## Parser

### Parser engine (src/intrpr/eng.py)

1. [DONE] Rewrite the parser to return an AST.

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

1. [DROPPED] Use temporary files to overcome the restriction in size of
io.StringIO buffers.
2. Rewrite the engine to fit the rewritten parser.
- Right now, I've made the parser return BinCmd, which is not going to be very
good for knowing if the STDOUT needs to output to a TTY or not. So, instead
the design needs to be changed in such a way that a CmdExpr node contains an
array of operators and an array of SimpCmd nodes. That way, the SimpCmd nodes
in the middle can see what operator is next to it.

### General utils and command API (src/utils/gen.py)

1. Implement kbhit(). See the issues file for more information.

## Command modules

### ls (src/bin/ls.py)

1. [DONE] Item type differentiation: Output different symbols for different
file types, as well as colour the output consistently.
2. [DONE] Number of inode links: Implement display of number of inode links.
Use `stat.st_nlink`.
