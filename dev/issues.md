# ISSUES

## Core interpreter

### Main entry point (src/main.py)

1. [DONE] inp() in still remains largely broken and missing core features.

### Interpreter engine (src/intrpr/eng.py)

1. Large text somehow makes io.StringIO buffers empty; I think this may be
because of the output length being larger than what is reported by the 8 bytes
after the first 4 bytes in the pipe between the forked and original process.

### Interpreter engine (NEW) (src/intrpr/eng_new.py)

1. The whole damn engine is fucking broken. It broke in so many places after
the refactor. The architecture feels and is more robust, but the implementation
is really shaky. It's crazy.
2. [DONE BUT NEEDS MORE WORK] (Implemented a workaround) Pipe from an external
command to a built-in command does not work.

### General utils and command API (src/utils/gen.py)

1. [DONE] inp(...): The way some codes are handled are incorrect. The "multiple
getch()" codes. Like, the ones for arrow keys. Without kbhit(), it's almost
impossible to guarantee that a keypress means a particular key.
2. inp(...): Sometimes raises an IndexError. I'm not sure of what I need to do
in order to reproduce it, but it's has happened twice or three times now, so
need to look out for that.
