# PLANNED

## Entry point

- Implement more powerful tab-completion. Context-aware, etc.

## Parser

### Parser engine (src/intrpr/eng.py)

- Implement globbing.

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

- [IRRELEVANT] [DROPPED] Use temporary files to overcome the restriction in
size of io.StringIO buffers.
- Improve aliases. Right now, it's very basic. You can alias only commands,
not commands and options or arguments or flags.

### General utils and command API (src/utils/gen.py)

- [DONE, NEEDS IMPROVEMENT] Implement tab completion.

## Command modules

### ls (src/bin/ls.py)

- Dynamically change the column lengths to maximise efficiency in using the
available space. Like, after calculating the number of columns, re-adjust the
column lengths after individual column lengths are found. Or something of that
sort.

### intrpr (src/intrpr/builtin_cmds/intrpr.py)

- Add colour for TTY output.
