# QUARK

Quark is a shell written in pure Python. It aims to be extensible and easy to
use.

See [`CHANGELOG.md`](./CHANGELOG.md) for a history of changes.  
See [`docs/`](./docs/) for detailed documentation on modules and internals.  
See [`dev/`](./dev/) for development notes and plans.  
See [`dev/planned.md`](./dev/planned.md) for future development plans and
ideas.  
See [`dev/issues.md`](./dev/issues.md) for bugs and issues in the project.

## Features

- Implemented in pure Python
- Two command systems (built-in and external)
- Extensible command system
- Live reload
- Powerful scripting system (Python)

## Quick start

Python 3.13 is required to run the shell from source.  
To run the shell from source, go to the project root and run:

```bash
git clone https://gitea.com/tkamaraj/quark.git/
cd ./quark/
python3 -m venv ./venv/
source ./venv/bin/activate
python3 -BOO ./src/main.py
```
or
```bash
chmod +x ./src/main.py
./src/main.py
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

Python 3.13 and Nuitka 4.0.8 are (currently) required for building the project.
See the full list of dependencies in `build_reqmts.txt`.

Go to the project root, and build the project with the build script `dev/pc.py`
(assuming the project is already cloned):

```bash
python3 -m pip install -r ./build_reqmts.txt
python3 -BOO ./dev/pc.py ./src/main.py
```

The help text is not available for the build script as of now, so please go
through the build script source to find out which options and flags are
available.

## Pre-built binaries

For pre-built binaries, check out the
[Releases](https://gitea.com/tkamaraj/quark/releases/) page.
