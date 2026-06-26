# ISSUES

## Core interpreter

### Interpreter engine (src/intrpr/eng.py)

- [DONE BUT NEEDS MORE WORK] (Implemented a workaround) Pipe from an external
command to a built-in command does not work.
- Recursion errors are weird. Like, when the command calls itself repeatedly.
I have no idea what is happening. But design, as of the commit on 25-05-2026,
the return code should be src.utils.err_codes.ERR_RNTIME_ERR. But the child
fails to send the error code through the pipe.
- Redirects do not work (think it's because of changing the outputs to pipes
to the parent process).
- Make the interpreter execute aliased commands

## Utilities

## Command modules

### Help command (src/intrpr/builtin_cmds/help.py)

- Difference in padding for different commands. Don't know why.

### Run in forked process command (src/bin/rf.py)

- [IRRELEVANT (STDERR is sent through pipe to parent now)] Debug statements
get mixed up in the output while executing the commands in the file. For
example, try running a file with the text "help\n" inside it as `rf ./scr.qrk`.
Won't happen every time, but often, because it seems to be a race between the
output text and the debug messages. I suspect it's due to the output being slow
to reach the parent process from the child process through the pipe.

### Process list command (src/bin/pl.py)

- The length of all the entries are calculated even when not using all the
entries, like when supplying arguments to filter processes. Modify the module
so that entries that are included the output only get their lengths calculated.
