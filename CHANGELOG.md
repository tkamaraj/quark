# CHANGELOG

## Latest commit

feat, refactor: command module ls

- `src/intrpr/builtin_cmds/rs.py`: Removed import of math module and changed
max_args from math.inf to float("inf")
- `src/bin/ls.py`: Internal restructure (don't know what else to call it) of
the command, with a new LsCtx (ls context) object added; Minor refactors and
code improvements; Added flags -t and --almost-all to suppress entries `.` and
`..`; Fixed a bug where slashes are not inserted at the end of directory names
by default due to a boolean error
- `src/intrpr/builtin_cmds/echo.py`: Changed the number of minimum arguments
from 0 to 1

## Commit b52c590d0a4d6213c6d8ea2c40cbc185fbe141f7

fix: load all modules in interpreter engine; chore: tweaked config values

- `src/intrpr/eng.py`: Changed how load all modules is handled in the
interpreter engine.
- `src/cfg.py`: Moved the prompt function to `src/utils/consts.py`, thus making
it the default.

## Commit dd2fc566b680c28740e06f7edb5295aeebaf4023

chore: clean up ignored files

## Commit 313f210292e17a159b7d9c3e56b32dad71daf3e8

chore: change gitignore

## Commit 234a134aa197b445e5d26b7406360686aafbfac0

chore: change default date format

- `src/bin/ls.py`: Changed default output date format.

## Commit dbf3841789622351db17acac3cc8527987ea6adc

fix: input function sequences; doc: added some documentation in same function

- `src/utils/gen.py`: Fixed a few special sequences not working in the input
function `inp(...)` due to indexing logic problems; Added some documentation in
the same function.

## Commit b2c1bb5217951568a8c7ab2a76a27c0248dea70c

feat: command cache

- `src/bin/cache.py`: Implemented the cache command.
- `src/bin/sl.py`: Minor, miscellaneous changes.

## Commit f882e982af26c94cc484eece265040935990012b

chore: add help object in module alias

- `src/bin/alias.py`: Added the help object.

## Commit 7808bcfea2e05080c52c301b3e6ad880712123c8

Basic alias functionality implemented; minor bug fixes and updates

- `README.md`: Updated and improved a few sections.
- `src/bin/ls.py`: Added a flag to keep formatting even when no TTY is
available.
- `src/utils/gen.py`: Minor bug fixes and changes in inp(...); added SIGSTOP
handling.
- `src/intrpr/eng.py`: Implemented aliasing.
- `src/intrpr/cfg_mgr.py`: Implemented alias support in the config file;
improved error reporting.

## Commit c8671553518104a1602f10e346492274ac90df78

fix: minor bug fixes, refactor: interpreter engine; ops: change interpreter
architecture; docs: general update; style: several changes, mainly in external
commands

- `src/intrpr/eng_new.py`: Removed old and dead methods from refactored engine; completed engine
refactor; switched refactored engine to default, main engine (renamed from
`src/intrpr/eng_new.py` to `src/intrpr/eng.py`); NOTE: the engine is still
incomplete.
- `src/utils/gen.py`: Implemented `kbhit()`, and wrote a class to handle input
specifically. Improved `inp(...)`.
- `src/intrpr/eng.py`: Moved to `src/old_vers/` under the name
`intrpr_eng_old_archi.py`.
- `src/parser/eng.py`: Moved to `src/old_vers/` under the name
`parser_eng_old_archi.py`.
- `src/bin/prn.py`: Minor changes and bug fixes.
- `src/bin/cnt.py`: Minor changes and improvements.
- Other miscellaneous improvements.

## Commit fd1b36880dac104cec93075d5d954f92b985a48c

Fixed the program not running due to refactors

## Commit c42eeafa8946f00b17cd9c43e2c9f5424352b818

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
