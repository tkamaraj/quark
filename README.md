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
python3 -BOO ./src/main.py
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
git clone https://gitea.com/tkamaraj/quark.git/
cd ./quark/
python3 -m venv ./venv/
source ./venv/bin/activate
python3 -m pip install -r ./build_reqmts.txt
python3 -BOO ./dev/pc.py ./src/main.py
```

The help text is not available for the build script as of now, so please go
through the build script source to find out which options and flags are
available.

## Pre-built binaries

For pre-built binaries, check the
[Releases](https://gitea.com/tkamaraj/quark/releases/) page.
