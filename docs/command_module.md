# WRITING A COMMAND MODULE

## Requirements for being considered a command module

Valid command modules for Quark require two compulsory variables, `HELP` and
`CMD_SPEC`, and one compulsory function, `run`, in the module scope. The
command module is rejected if these attributes are not present in the module.

## Types of compulsory attributes in the command module

Variable `HELP` must be an object of type `utils.HelpObj` or a subclass of it.
Variable `CMD_SPEC` must be an object of type `utils.CmdSpec` or a subclass of
it. Function `run` must accept only one parameter, preferrably called `data`,
of type `utils.gen.CmdData`, and return an `int`, which will be the exit code
of the command. All these types are enforced by the command resolver, which
will reject the command module if a discrepancy is encountered.

## API

The command API is provided by `utils.gen`. Command authors are encouraged not
to access core modules of the interpreter. Refer to
[this page](<insert link of utils.gen docs you idiot>) for documentation on the
API.

Common error codes are provided in `utils.err_codes`. Command authors are
encouraged to use the error codes listed in this file if their use case is
available. To get a list of error codes available, use the `utils.gen.`
function. (TODO: Implement that!)

## Notes

Other functions, classes and variables are allowed at the module level. Only,
make sure that their names do not clash with the compulsory module-level
attributes.
