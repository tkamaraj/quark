#!/usr/bin/env -S python3 -BOO
import pickle
import sys

try:
    raise NameError("Hello")
except NameError as e:
    print(e.__traceback__)
    x = pickle.dumps(sys.exc_info())

print(pickle.loads(x))
