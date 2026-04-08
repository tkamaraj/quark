# CHANGELOG

## Latest commit

[COMMIT NAME]

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
