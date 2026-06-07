# ISSUES

## Core interpreter

### Main entry point (src/main.py)

1. [IRRELEVANT] [DONE] inp() in still remains largely broken and missing core
features.

### [IRRELEVANT] Old interpreter engine (OLD ARCHITECTURE) (src/old_vers/intrpr_eng_old_archi.py)

1. Large text somehow makes io.StringIO buffers empty; I think this may be
because of the output length being larger than what is reported by the 8 bytes
after the first 4 bytes in the pipe between the forked and original process.

### Interpreter engine (src/intrpr/eng.py)

1. [DONE] The whole damn engine is fucking broken. It broke in so many
places after the refactor. The architecture feels and is more robust, but the
implementation is really shaky. It's crazy.
2. [DONE BUT NEEDS MORE WORK] (Implemented a workaround) Pipe from an external
command to a built-in command does not work.
3. Recursion errors are weird. Like, when the command calls itself repeatedly.
I have no idea what is happening. But design, as of the commit on 25-05-2026,
the return code should be src.utils.err_codes.ERR_RNTIME_ERR. But the child
fails to send the error code through the pipe.
4. Redirects do not work (think it's because of changing the outputs to pipes
to the parent process).

### Command resolver (src/intrpr/cmd_reslvr.py)

1. The command resolver successfully resolves lines like "./ls" to "ls". This
shouldn't happen. It happens because the paths are resolved with Path.resolve()
and hence "./ls" gets converted to "ls", which invokes the ls command. Make the
command resolver not resolve the path when searching for a command, as
resolution of the path is not needed for searching.

### Interpreter internals (src/intrpr/internals.py)

1. Shared memory does not fucking work. I've got no idea why. Fuck me. After so
much time and effort implementing it, just for it to not work. Changes do not
get reflected. That's the problem.
2. Lock needs be in the interpreter object so that it's shared instead of being
separate for each process

### Logger (src/logger/)

1. Implement per-logger levels.

## Utilities

### General utilities and command API (src/utils/gen.py)

1. [DONE] inp(...): The way some codes are handled are incorrect. The "multiple
getch()" codes. Like, the ones for arrow keys. Without kbhit(), it's almost
impossible to guarantee that a keypress means a particular key.
2. [DONE] inp(...): Sometimes raises an IndexError. I'm not sure of what I need
to do in order to reproduce it, but it's has happened twice or three times now,
so need to look out for that.
3. [DONE] inp(...): alt+d does not seem to work properly. Something broke
during the getch() re-design and kbhit() implementation.
4. [DONE] inp(...): ^w raises IndexError.

## Command modules

### Help command (src/intrpr/builtin_cmds/help.py)

1. Difference in padding for different commands. Don't know why.

### Run in forked process command (src/bin/rf.py)

1. [IRRELEVANT (STDERR is sent through pipe to parent now)] Debug statements
get mixed up in the output while executing the commands in the file. For
example, try running a file with the text "help\n" inside it as `rf ./scr.qrk`.
Won't happen every time, but often, because it seems to be a race between the
output text and the debug messages. I suspect it's due to the output being slow
to reach the parent process from the child process through the pipe.

### Process list command (src/bin/pl.py)

1. The length of all the entries are calculated even when not using all the
entries, like when supplying arguments to filter processes. Modify the module
so that entries that are included the output only get their lengths calculated.

### List directory command (src/bin/ls.py)

1. [DONE] Quotes surrounding names with special characters get coloured. They
should not be.
2. [DONE] Try to put in a space before the names without surrounding quotes if
its column contains a name with surrounding quotes.

### System command module (src/intrpr/builtin_cmds/cmd.py)

1. [DONE] UnicodeDecodeError when reading a non-text file (you know what I
mean).

### Alias command module (src/intrpr/builtin_cmds/alias.py)

1. [DONE] Implement alias setting for session.
