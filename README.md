# QUARK

Quark is a shell written in pure Python. It aims to be extensible and easy to
use. It supports minimal scripting with its own scripting language. For
advanced scripting, it uses Python.

## Usage

Use the `-h` flag with the main program for the help text.

## Building

Nuitka 4.0.5 is (currently) required for building the project. See the full
list of requirements in `src/build_reqmts.txt`.

Go to the project root, and build the project as:

    python -BOO ./dev/pc.py ./src/main.py

~~See `python ./dev/pc.py -h` for help.~~ The help text is not available as of
now, so please go through the source to find out which options and flags are
available.

## Pre-build binaries

For pre-built binaries, check the
[Releases](https://github.com/tkamaraj/quark1/releases/) page.

## Project structure

(File structure view obtained from `tree --charset=ASCII --filesfirst ./src/`)

```
./src/
|-- cfg.py
|-- main.py
|-- bin
|   |-- cnt.py
|   |-- cp.py
|   |-- head.py
|   |-- ls.py
|   |-- pl.py
|   |-- prn.py
|   |-- rand.py
|   |-- rn.py
|   |-- stat.py
|   |-- test.py
|   `-- whoami.py
|-- intrpr
|   |-- cfg_mgr.py
|   |-- cmd_reslvr.py
|   |-- eng.py
|   |-- __init__.py
|   |-- internals.py
|   `-- builtin_cmds
|       |-- cd.py
|       |-- clear.py
|       |-- echo.py
|       |-- exec.py
|       |-- exit.py
|       |-- false.py
|       |-- get.py
|       |-- help.py
|       |-- __init__.py
|       |-- pwd.py
|       |-- set.py
|       |-- src.py
|       |-- true.py
|       `-- which.py
|-- parser
|   |-- eng.py
|   |-- __init__.py
|   `-- internals.py
`-- utils
    |-- consts.py
    |-- debug.py
    |-- engine_utils.py
    |-- err_codes.py
    |-- gen.py
    |-- __init__.py
    `-- loggers.py
```
