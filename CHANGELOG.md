# CHANGELOG

## Latest commit 

Interpreter engine rewrite (INCOMPLETE)

- `src/eng_new.py`: Copied the engine and edited it to accommodate the new
parser output. The original parser has not been changed. Only a copy of the
original parser has been changed and is named `src/parser/eng_new.py`. This
interpreter engine is unfinished and will not run.
- Documentation updates.

## Commit 39a9fb2feb61bec80af858bb1922eacd2b5dd121

Parser re-design; fixed bugs

- `src/parser/`: Completely re-designed the parser. The parser now returns an
AST.
- `src/intrpr/builtin_cmds/hist.py`: Fixed bugs, added a flag.
- `src/utils/gen.py`: Fixed a bug in inp(...) that I (rather stupidly)
accidentally included.

## Commit dd3203de2c875b9d00f3acc4b9bd617da32f8739

Completed inp(); command history implemented; command module hist implemented;
renamed a few commands

- `src/utils/gen.py`: Completed inp() (mostly) and fixed major bugs. Moved it
and related functions to `src/utils.gen.py` from `src/main.py`.
- Renamed a few commands.
- Command history implemented.
- `src/intrpr/builtin_cmds/hist.py`: Implemented `hist` for accessing history.
- Documentation updates.

## Commit ce2b2171fa2146f8a96ffbe6643b25494749ce62

Planned features were added; made UX improvements; implemented command cmd

- `dev/pc.py`: Made minor changes
- `src/bin/ls.py`: Added in planned feature (inclusion of a flag for the
display of number of inode links)
- `src/bin/test.py`: Added in the help strings in the help object of the test
command (development purposes only)
- `src/intrpr/builtin_cmds/get.py`: Modified to pad only when STDOUT is a TTY
- `src/intrpr/builtin_cmds/cmd.py`: Started writing, and is suspended, because
I don't know how to handle the output. Just letting it do its thing without
capturing output does not work, because it does not obey redirection that way
and I don't know what else. This current thing I do is... wrong, but I can find
no other way to do it. I capture the output and write them later, which is
incorrect because the program might output on STDERR and STDOUT alternatively,
and the order, therefore, isn't preserved. Also, I have no idea how I'm going
to output to STDERR without a header, because all the damn loggers have headers
- Minor touchups here and there

## Commit 3b9b5728782b096782114e945a956d277dd32d61

Made visual changes and added in a command module

- `src/bin/ls.py`: Removed tightening padding by using column maximum lengths.
It makes the output look ridiculous for some directories, as the algorithm
currently in use does not use space available to the maximum extent.
- `src/bin/stat.py`: Started writing and finished the command module.

## Commit 7fe4950cf0d994f86e295c1e697cc4aceca7ec15

Initial commit; version 0.1
