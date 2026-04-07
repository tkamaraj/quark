# PLANNED

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

1. [DROPPED] Use temporary files to overcome the restriction in size of
io.StringIO buffers.

## Command modules

### ls (src/bin/ls.py)

1. [DONE] Item type differentiation: Output different symbols for different
file types, as well as colour the output consistently.

2. Number of inode links: Implement display of number of inode links. Use
`stat.st_nlink`.
