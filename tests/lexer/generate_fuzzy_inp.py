#!/usr/bin/env -S python3 -BOO
import os
import random as ran
import sys
import time

called_nm = __file__
num_tests = 1000
len_test = 1000
#        9 -> Horizontal tab (\t)
#       10 -> Linefeed (\n)
# 32 - 127 -> Printable characters
chs = tuple(chr(i) for i in (9, 10, *range(32, 128)))

if len(sys.argv) not in (1, 3):
    raise ValueError("Invalid argument array length")
for i, arg in enumerate(sys.argv):
    if i == 0:
        called_nm = arg
    if arg == "-":
        continue
    if i == 1:
        num_tests = int(arg)
    elif i == 2:
        len_test = int(arg)

out_dir = os.path.join(os.path.dirname(__file__), f"{time.time_ns():x}")
try:
    os.makedirs(out_dir)
except OSError as e:
    sys.stderr.write(f"OS error; {e.strerror}: {out_dir}")
    sys.exit(1)

one_less_len_num_tests = len(str(num_tests)) - 1
for test_num in range(num_tests):
    test_chs = []
    for i in range(len_test):
        test_chs.append(ran.choice(chs))
    flnm = os.path.join(out_dir, f"test_{test_num:>0{one_less_len_num_tests}}")
    try:
        with open(flnm, "w") as f:
            f.write("".join(test_chs))
    except OSError as e:
        sys.stderr.write(f"OS error; {e.strerror}: {flnm}")
        sys.exit(2)
    print(f"Generated test number {test_num + 1}")
