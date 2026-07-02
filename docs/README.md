# QUARK

An extensible pure Python shell.

See [`CHANGELOG.md`](./CHANGELOG.md) for a history of changes.  
See [`docs/`](../docs/) for detailed documentation on modules and internals.  
See [`dev/`](../dev/) for development notes and plans.  
See [`dev/planned.md`](../dev/planned.md) for future development plans and
ideas.  
See [`dev/issues.md`](../dev/issues.md) for bugs and issues in the project.

## About

Quark is a command-line interpreter ("shell") that focuses on 

## Highlights

- Written from scratch depending only on the standard library
- Custom lexer and parser

## Features

- Interactive command-line interface
- Built-in and external commands
- Extensible command system
- Live reload
- Powerful and large scripting system (Python)
- Alias support
- Interpreter and environment variable system
- Piping and redirection
- Command history
- Tab completion
- Configurable

## Quick start: running from source

Python 3.13 or later is required for running the program from source.  
To run the shell from source:

```shell
git clone https://gitea.com/tkamaraj/quark.git
cd ./quark/
python3 -m venv ./venv/
source ./venv/bin/activate
python3 -BOO ./src/main.py
```

Use the `-h` flag with the main program for the help text.  
Example commands:

```
help -a
ls -la
cd ../
echo -s , hello world
```

## Building from source

Python 3.13 and Nuitka 4.0.8 are required for building the project.  
See the full list of dependencies in `build_reqmts.txt`.

Go to the project root, and build the project with the build script `dev/pc.py`
(assuming the project was already cloned and virtual environment activated):

```shell
python3 -m pip install -r ./build_reqmts.txt
python3 -BOO ./dev/pc.py ./src/main.py
```

The help text is not available for the build script as of now, so please go
through the build script source to find out which options and flags are
available.

## Pre-built binaries

For pre-built binaries, check out the
[Releases](https://gitea.com/tkamaraj/quark/releases/) page.

## Configuration

Use the `-h` or `--help` flag with the main program for a list of available
parameters that can passed to the program.

The configuration file, `cfg.py`, is located in the same directory where the
main program is.  
Configuration options available:

```python
ALIASES: dict[str, str] = {}
PTH: tuple[str, ...] = (USR_PY_PTH, *SYS_PY_PTHS, PY_PTH)
PROMPT: str | typing.Callable[[intrpr.internals.IntrprTbl], str] = utils.consts.Defaults.PROMPT
LN_MODE: str = "emacs"
```

## Project status

The project is still in development, and may contain a *lot* of bugs. Use at
your own risk.

## Contributing

This project does not currently accept any contributions.
