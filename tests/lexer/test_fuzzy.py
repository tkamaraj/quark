#!/usr/bin/env -S python3 -BOO
import os
import sys
import traceback as tb
from src.parser import eng as peng

if len(sys.argv) < 2:
    raise ValueError("Expected at least one test")

parser = peng.Parser()
cwd = os.getcwd()
for arg in sys.argv[1 :]:
    results = []
    normed_arg = os.path.normpath(arg)
    for item in sorted(os.scandir(arg), key=lambda entry: entry.name):
        try:
            if not item.is_file():
                continue
            with open(item) as f:
                try:
                    parser.get_cmd_seq(f.read(), cwd)
                    results.append(f"-> {item.name} of {normed_arg}: PASS")
                except Exception:
                    tb.print_exc()
                    results.append(
                        f"-> {item.name} of {normed_arg}: FAIL\n"
                        + "\n".join(("   " + i) for i in tb.format_exc().strip().split("\n"))
                    )
            print(f"Tested {item.name} of test {normed_arg}")
        except OSError as e:
            sys.stderr.write(f"OS error; {e.strerror}: {item.name} of {normed_arg}")
        except KeyboardInterrupt:
            break
    with open(f"./{os.path.basename(normed_arg)}_results.txt", "w") as f:
        f.write("\n".join(results) + "\n")
