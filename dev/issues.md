# ISSUES

## Core interpreter

### Main entry point (src/main.py)

1. [DONE] inp() in still remains largely broken and missing core features.

### Interpreter engine (src/intrpr/eng.py)

1. Large text somehow makes io.StringIO buffers empty; I think this may be
because of the output length being larger than what is reported by the 8 bytes
after the first 4 bytes in the pipe between the forked and original process.

### General utils and command API (src/utils/gen.py)

1. inp(...): The way some codes are handled are incorrect. The "multiple
getch()" codes. Like, the ones for arrow keys. Without kbhit(), it's almost
impossible to guarantee that a keypress means a particular key.
