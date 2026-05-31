# CHANGELOG

## Latest commit

feat: hash checks for cache, module paths in cache

- `src/intrpr/cmd_reslvr.py`: Included hash checks for command cache; added
module path to cache data
- `src/utils/err_code.py`: Added a new error code, ERR_UNK_ERR, for unknown
errors

## Commit 61af21329b7850615c3b3e8fe0b0ad0e832eba40

fix: removed unnecessary pass of cached external commands to builtin gatherer

- `src/intrpr/cmd_reslvr.py`: Removed unnecessary passage of cached external
commands dictionary to builtin commands gatherer method

## Commit b78ff5ccd22ef0befefc09f4c53e71b3b7ef58a6

feat: command validation for help; fix: undefined name in command module ls

- `src/intrpr/cmd_reslvr.py`: Added a command validation method and made help
object to be provided only if a valid command module is found; minor formatting
changes
- `src/bin/ls.py`: Fixed minor NameError bug in no TTY branch
- `src/intrpr/builtin_cmds/help.py`: Minor formatting changes

## Commit 5dc5c1c625c284722c630ed3eec2c649998f2582

fix: multiline descriptions in command module help

- `src/intrpr/builtin_cmds/help.py`: Fixed multiline descriptions not getting
padded properly
- `src/intrpr/eng.py`: Minor changes

## Commit 70f594e6da9d917f594a0bf6c39c2caaafa6234e

feat: implement command module time

- `src/intrpr/builtin_cmds/time.py`: Implemented command module time

## Commit ebbbb92ea172cefa92cc21a4d291f9d55e85f2fc

fix: unhandled IsADirectoryError command module head

- `src/bin/head.py`: Fixed unhandled IsADirectoryError

## Commit d6621fc2a5b29927707446d9c48504e433148175

docs: update command module ls section

- `dev/issues.md`: Update command module ls section

## Commit 4a21321d50b83decdd0ef08242912e0f230b202a

refactor, fix: command module ls

- `src/bin/ls.py`: Major refactor; Fixed formatting bugs; Added option for
adjusting padding (-p, --padding)

## Commit 2ae30ac00174b8208a97019dacef99f00008bea8

fix: missing argument to config object

- `src/intrpr/cfg_mgr.py`: Resolved missing argument to configuration object

## Commit 81094e414774b3af77f1e91af8893b07615105bc

feat: input command module read; fix: unnecessary call in command module set

- `src/intrpr/builtin_cmds/read.py`: Created and finished the input command
module read
- `src/intrpr/builtin_cmds/set.py`: Removed unnecessary ast.literal_eval(...)
call and removed import of module ast from stdlib

## Commit 85c04f96138da53853d57f1a3872fe186073ed46

fix: unresolved import in interpreter internals

- `src/intrpr/internals.py`: Fixed NameError due to unresolved import

## Commit f8cd4c3c91e33b96d1da9fa9605d19845d28b273

refactor: exception info flow

- `src/intrpr/eng.py`: Changed how the exception info flows from the child to
the parent. Now, the whole exception object is transferred through the pipe by
pickling, with a thin wrapper to compensate for a few fields dropped during
the pickling process; Minor name bugfix

## Commit bb2db99cd4f522fb28aec6c394ac5298c8c3945f

fix: handling of uncontrolled recursive calls, module cmd; docs: issues update

- `src/intrpr/eng.py`: Used the traceback message sent for uncaught exceptions
in external commands; Improved handling and error message display of
commands doing uncontrolled interpreter invokations (don't know what else to
call it); Handled too many files open when compiled (when opening pipes)
- `src/intrpr/builtin_cmds/cmd.py`: Fixed STDERR from system interpreter being
displayed through this interpreter's logging system (like, with headers and
everything)
- `src/utils/err_codes.py`: Added an interpreter error code

## Commit 2168e8b54e111b073ad381186b2196128ba51082

build: change display paths

- `dev/pc.py`: Changed display paths a bit

## Commit dac4d793a52f88fe96bc6f016fe9b869f485c8e6

fix: minor command module bugfixes

- `src/intrpr/builtin_cmds/cmd.py`: Handled overlooked UnicodeDecodeError case
- `src/intrpr/builtin_cmds/rs.py`: Handled overlooked UnicodeDecodeError case
- `src/bin/rf.py`: Handled overlooked UnicodeDecodeError case

## Commit 01ecffc4c7cfe79454dae1005a9e212e9afb7923

- `dev/pc.py`: Changed Python invoke name from "python" to "python3"

## Commit 01ecffc4c7cfe79454dae1005a9e212e9afb7923

refactor: interpreter engine; fix: no output bug in command module ls

- `src/intrpr/eng.py`: Major rewrite; Refactors for external command execution;
Changed data streaming processes; Made STDERR to be transferred through a pipe,
too, similar to STDOUT from the child process; Streaming both STDOUT and STDERR
at the same time
- `src/bin/ls.py`: Fixed the command not producing output following an error
with a previous argument
- `src/utils/err_codes.py`: Changed an error code's name
- `src/utils/gen.py`: Removed unnecessarry function log_to_fl(...)
- `src/intrpr/cmd_reslvr.py`: Removed calls to src.utils.gen.log_to_fl(...)

## Commit c0f99742554f805b39ed7969a73d3576fc3835bd

attempt fix: shell engine failure due to recursive command invokation (FAILED)

## Commit e9c676b84c08f3709b82f02c02c8ba2ec76bd9ba

fix: unresolved import in command module rand

- `src/bin/rand.py`: Resolved a NameError bug due to an unresolved import

## Commit 39574a4341ff5bf1b79370d86bac076240628c3a

chore: remove .gitignore from tracked files

## Commit 162c6e8b30a56e2cec7188ebd3a5a11c25dce1cc

fix: logic errors in prompt resolution and redirection

- `src/main.py`: Renamed a variable
- `src/intrpr/eng.py`: Resolved a NameError bug in redirection logic; Fixed
logical errors in prompt resolution and added an error message for invalid type
of prompt variable

## Commit 19ce7770c4112beb940e9544b78af57d95f52010

fix: transport endpoint bug in command module ls

- `src/bin/ls.py`: Fixed several undefined and unbound variable bugs; Fixed
an OSError problem of other items in a directory not getting listed for an
transport endpoint not being connected
- `src/parser/eng.py`: Fixed a TypeError bug due to no type checks

## Commit fffe490a6c9a48d293f4afbf12dba05abf55fa0e

merge: branch input to branch master

## Commit 5205691c16a0fe944005f076f938776b1c1ccae1

feat: add compiler to build script; fix: search paths

- `dev/pc.py`: Added flag to use clang

## Commit fbee4ff1450af28266384b02eb4c747a5c577997

feat, refactor: line modes

- `src/main.py`: Changed the input and line mode handler to `readline` from
Python's standard library; added modes "emacs", "vi" and "raw"

## Commit 5f5a8efe930ded1238fb52bf54193e71a4d03a6a

chore: miscellaneous changes to several files

## Commit 90ae12e291b863966e048f70b23dc885495bffe6

docs: changelog and issues update

## Commit f68f7cb39e67b20f4e34352fdcfb928666be3141

add .gitignore to tracked files

## Commit 64abdf16a4a9216bd2ec022a94b496032def8f03

docs: fixed typo and sentence structure, restructured doc pages, added content

- `docs/archi.md`: Moved some sections from README, added content, updated
content
- `README.md`: Corrected typo, and moved some sections to other doc pages,
- `docs/cmd_mod.md`: Changed a few sentences

## Commit 6184abdcd35df1ce049c86cea9e8e4c7e2e5d1fb

build: added option to Nuitka call

- `dev/pc.py`: Added an option in the Nuitka call to stop Nuitka from stopping
the program with the `-c` option. No idea why, but it says that the program
tried to call itself, and suggested this option

## Commit 57f47291c284f7617ddb7e967eb8655b13ddb484

fix: child process interrupt bug

- `src/intrpr/eng.py`: Fixed bug where interrupt in child process would raise
AttributeError due to None being passed to the parent to be killed in place of
the child's PID

## Commit 52aba7ee53b00e36ead03ae7ee98e8e8e10b30c8

fix: general utils file logging

- `src/utils/gen.py`: Incomplete file logging improvements

## Commit 22527e04a3fe331556d9184cd966d15ba8f3964a

fix: command module alias order of output and error messages

- `src/intrpr/builtin_cmds/alias.py`: Fixed output and error messages not
respecting argument order

## Commit e777b4e3d33d69118ba977c41c5b33e17246bb65

fix: logging function NameError bugs

- `src/utils/gen.py`: Fixed NameError bugs in logging functions

## Commit 2a195d7110ca3b8ef45f5acce645396432524219

feat: source info for all log levels; fix: interpreter engine return code
unpack

- `src/intrpr/eng.py`: Fixed unpack errors for external command return code
- `src/utils/gen.py`: Added source info for debug, info, warn, crit and fatal

## Commit e2ff7cebae373f8573046a04afac66d139b106f2

feat: added source info in logging

- `src/utils/gen.py`: Added source info in logging
- `src/bin/`, `src/intrpr/builtin_cmds/`: Edited logging function calls to
include source info

## Commit 0e155c93c7ed0194365b04734ca9a40ca57199c9

refactor: command module set; fix: general utils logging

- `src/intrpr/builtin_cmds/set.py`: Refactor and fixed bugs; now accommodates
NoneType
- `src/utils/gen.py`: Fixed NameError bug in logging functions

## Commit 0a31a6d6b6da8cb46f4df2032b4da407495ace8b

feat: delete variable in command module set; refactor: command module set

- `src/intrpr/builtin_cmds/set.py`: Refactored. Added support for deleting
variables.

## Commit 72d98233916fbde7c60eef9a5e0a1c50144b89c5

fix: history command hist

- `src/intrpr/builtin_cmds/hist.py`: Now returns immediately if no flags are
specified

## Commit 114a71d154ac29148c8eb100a4fdd4233a72153b

chore: removed src/cfg.py (unneeded)

- `src/cfg.py`: Removed; unnecessary file, no idea how it came up here

## Commit b922b568557136fb96471dee4d780955be03ed5a

feat: custom logger; fix: alias command output

- `src/intrpr/builtin_cmds/echo.py`: Removed unnecessary import
- `src/logger/`: Finished custom logger
- `src/main.py`, `src/utils/gen.py`: Integrated custom logger
- `src/utils/consts.py`: Updated var SP_CHRS
- `src/intrpr/builtin_cmds/alias.py`: Removed extra character from output

## Commit bb54ad79d0d0c03b40b83ba720d354c3b3df94a4

docs: fixed README

- `README.md`: Minor link corrections.

## Commit 2ffa755a79cf80b05c849cd32e72d67cf29b08a4

fix: command modules stat and pl

- `src/stat.py`: Changed flag parsing; added item name display before stat
output.
- `src/pl.py`: Fixed help string.

## Commit 1be7a7bce1e9e805eed19231855731e17c68361b

docs: update releases link

- `README.md`: Update releases link from GitHub to Gitea.

## Commit 15174a9ee2e65b6f776cb3beadbaabc2be152b84

feat: command module pl process filtering

- `src/bin/pl.py`: Added process filtering.

## Commit 0ca6ba44f6c21c457a167d0a29233f24dcc66d54

perf: command module ls

- `src/bin/ls.py`: Slight performance-related change (maybe noticable for large
directories)

## Commit a9bce692b03d02b7928b0517ef24e36354115610

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
