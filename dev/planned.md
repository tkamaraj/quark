# PLANNED

## Parser

### Parser engine (src/intrpr/eng.py)

1. [DONE] Rewrite the parser to return an AST.
2. Implement globbing.

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

1. [IRRELEVANT] [DROPPED] Use temporary files to overcome the restriction in
size of io.StringIO buffers.
2. [DONE] Rewrite the engine to fit the rewritten parser.
    - [DONE] Right now, I've made the parser return BinCmd, which is not going
to be very good for knowing if the STDOUT needs to output to a TTY or not. So,
instead the design needs to be changed in such a way that a CmdExpr node
contains an array of operators and an array of SimpCmd nodes. That way, the
SimpCmd nodes in the middle can see what operator is next to it.
3. [DONE] Implement aliases.
4. Improve aliases. Right now, it's very basic. You can alias only commands,
not commands and options or arguments or flags.

### General utils and command API (src/utils/gen.py)

1. [DONE] Implement kbhit(). See the issues file for more information.
2. Implement tab completion.

## Command modules

### ls (src/bin/ls.py)

1. [DONE] Item type differentiation: Output different symbols for different
file types, as well as colour the output consistently.
2. [DONE] Number of inode links: Implement display of number of inode links.
Use `stat.st_nlink`.

### pl (src/bin/pl.py)

1. [DONE] Add process filtering.
