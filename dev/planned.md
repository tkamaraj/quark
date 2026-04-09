# PLANNED

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

1. [DROPPED] Use temporary files to overcome the restriction in size of
io.StringIO buffers.

### General utils and command API (src/utils/gen.py)

1. Implement kbhit(). See the issues file for more information.

## Command modules

### ls (src/bin/ls.py)

1. [DONE] Item type differentiation: Output different symbols for different
file types, as well as colour the output consistently.
2. [DONE] Number of inode links: Implement display of number of inode links.
Use `stat.st_nlink`.
