# INTERPRETER ARCHITECTURE

## Control flow

```
Main program (user input)
   |
Parser
   |
Interpreter engine
   |
Execution
   |
Main program
```

## Project structure

(File structure view obtained from `tree --gitignore --charset=ascii ./src/`)

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

The core interpreter (`src/intrpr/`) is divided into three parts:

- `src/intrpr/cmd_reslvr.py`: The command resolver, for command resolution
- `src/intrpr/cfg_mgr.py`: The config manager, for loading and managing the
configuration file
- `src/intrpr/eng.py`: The "engine" of the interpreter, which houses the
interpreter object itself (`Intrpr`)

The parser (`src/parser/`) is divided into three parts:

- `src/parser/eng.py`: Houses the main parser object
- `src/parser/ast_nodes.py`: Contains AST node definitions
- `src/parser/internals.py`: Contains parser-specific attributes and data

`src/utils/` contains modules that are required all over the project.

- `src/utils/consts.py`: Houses constants used by various parts of the project
- `src/utils/debug.py`: Contains debugging facilities
- `src/utils/err_codes.py`: Provides common errors codes that can be used by
command modules.
- `src/utils/gen.py`: Provides the API for commands to interact with the
interpreter.
- `src/utils/loggers.py`: NOTE: Not used now. Contains the loggers from the
standard library logging module.
