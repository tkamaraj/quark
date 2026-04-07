# WRITING A COMMAND MODULE

## Requirements for being considered a command module

Valid command modules for Quark require two compulsory variables, `HELP` and
`CMD_SPEC`, and one compulsory function, `run`, in the module scope. The
command module is rejected if these attributes are not present in the module.

## Types of required attributes in the command module

Variable `HELP` must be an object of type `utils.HelpObj` or a subclass of it.
Variable `CMD_SPEC` must be an object of type `utils.CmdSpec` or a subclass of
it. Function `run` must accept only one parameter of type `utils.gen.CmdData`,
and return an `int`, which will be the exit code of the command. All these
types are enforced by the command resolver, which will reject the command
module if a discrepancy is encountered.

## API

The command API is provided by `utils.gen`. Command authors are encouraged not
to access core modules of the interpreter. The documentation for the API is not
available right now.

Common error codes are provided in `utils.err_codes`. Command authors are
encouraged to use the error codes listed in this file if their use case is
available. To get a list of error codes available, use the FUNCTION function.
(TODO: Implement that!)

## Notes

Other functions, classes and variables are allowed at the module level. Only,
make sure that their names do not clash with `HELP`, `CMD_SPEC` and `run`.

When a command is invoked:

1. The command module is loaded
2. The module is validated based on if it contains the required attributes and
the type of the attributes
3. The `run` function is extracted, and called with a `CmdData` object passed
to it. It is called in a forked process if it is an external command, or the
same process as the interpreter if it is a built-in command
4. The integer returned by `run` is considered the exit code of the command,
which is assigned to the environment variable `_LAST_RET_`.

## Example

```python
import utils.err_codes
import utils.gen

HELP = utils.gen.HelpObj(
    usage="test [flag ...] [opt] arg [...]",
    summary="Example summary",
    details=(
        "ARGUMENTS",
        ("arg", "Description of arg blah blah blah"),
        "OPTIONS",
        ("-opt val", "Description of opt"),
        "FLAGS",
        ("-f, --flag", "Some flag, whatever"),
        ("-flag2", "Some other flag, whatever")
    )
)

CMD_SPEC = utils.gen.CmdSpec(
    min_args=1,
    max_args=float("inf"),
    opts=("-opt",),
    flags=("-f", "-flag", "-flag2")
)


def run(data: utils.gen.CmdData) -> int:
    return utils.err_codes.ERR_ALL_GOOD
```
