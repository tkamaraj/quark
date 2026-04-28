#!/usr/bin/env -S python3 -BOO
import atexit
import os
import select
import sys
import termios
import tty


class InpHdlr:
    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.old_sett = termios.tcgetattr(self.fd)
        atexit.register(self.reset_sett)

    def set_new_sett(self):
        tty.setraw(self.fd)

    def reset_sett(self) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_sett)

    def kbhit(self, timeout=0):
        r, _, _ = select.select([self.fd], [], [], timeout)
        return bool(r)

    def getch(self) -> str:
        return os.read(self.fd, 1).decode()


def test():
    h = InpHdlr()
    h.set_new_sett()
    k = h.getch()
    if k == "\x03":
        return
    while h.kbhit():
        k += h.getch()
    return k


while 1:
    k = test()
    if k is None:
        break
    print(repr(k))
