# QUARK

Quark is a shell written in pure Python. It aims to be extensible and easy to
use. It supports top-to-bottom execution of commands from a file. For advanced
scripting, it uses Python.

See [`CHANGELOG.md`](./CHANGELOG.md) for a history of changes.  
See [`docs/`](./docs/) for detailed documentation on modules and internals.  
See [`dev/`](./dev/) for development notes and plans.  
See [`dev/planned.md`](./dev/planned.md) for future development plans and
ideas.

## Features

- Custom shell implemented in pure Python
- Built-in commands
- Extensible command system
- Mature scripting system (Python)

## Quick start

To run the shell from source, go to the project root and run:

```bash
python -BOO ./src/main.py
```

Use the `-h` flag with the main program for the help text.  
Example commands:

```
ls -la
cd ../
echo -s haha foo bar
```

## Building from source

Nuitka 4.0.8 is (currently) required for building the project. See the full
list of requirements in `build_reqmts.txt`.

Go to the project root, and build the project with the build script,
`dev/pc.py`:

```bash
git clone https://github.com/tkamaraj/quark/
cd ./quark/
python -m venv ./venv/
source ./venv/bin/activate
python -m pip install -r ./build_reqmts.txt
python -BOO ./dev/pc.py ./src/main.py
```

The help text is not available for the build script as of now, so please go
through the build script source to find out which options and flags are
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
|   `-- ...
|-- intrpr
|   |-- cfg_mgr.py
|   |-- cmd_reslvr.py
|   |-- eng.py
|   |-- __init__.py
|   |-- internals.py
|   `-- builtin_cmds/
|       `-- ...
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

The interpreter has three major parts:

- `src/main.py`: The main program, contains the main interpreter loop
- `src/parser/`: The parser, contains the parser (duh!)
- `src/intrpr/`: The core interpreter, contains logic to execute commands

The core interpreter is divided into three parts:

- `src/intrpr/cmd_reslvr.py`: The command resolver, for command resolution
- `src/intrpr/cfg_mgr.py`: The config manager, for loading and managing the
configuration file
- `src/intrpr/eng.py`: The "engine" of the interpreter, which houses the
interpreter object itself (`Intrpr`)

`src/utils/` contains modules that are required all over the project.
`src/utils/gen.py` provides the API for commands to interact with the
interpreter. `src/utils/err_codes.py` provides common errors codes that can be
used by commands.
