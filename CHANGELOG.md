# CHANGELOG

## Latest commit

[COMMIT NAME]

- `src/bin/ls.py`: Removed tightening padding by using column maximum lengths.
It makes the output look ridiculous for some directories, as the algorithm
currently in use does not use space available to the maximum extent.
- `src/bin/stat.py`: Started writing and finished the command module.

## Commit 7fe4950cf0d994f86e295c1e697cc4aceca7ec15

Initial commit; version 0.1
