import os
import runpy as rp
import typing as ty

import utils.consts as uconst
import utils.gen as ugen
import utils.err_codes as uerr


class Cfg(ty.NamedTuple):
    prompt: str
    pth: tuple[str]


def sandbox_runpy(fl: str) -> dict[str, ty.Any] | None:
    """
    Actually get the config from the configuration file.
    I don't know if this is actually sandboxing the load of the config file.
    Need to test. TODO!

    :param fl: Configuration filepath.
    :type fl: str

    :returns: Config module's globals dictionary.
    :rtype: dict[str, typing.Any] | None
    """
    try:
        return rp.run_path(fl)
    except FileNotFoundError:
        return None


def get_cfg() -> Cfg:
    """
    TODO: Fill up!
    ???

    :returns: Config object containing values from the config file, if valid,
              else default values.
    :rtype: Cfg
    """
    prompt = uconst.Defaults.PROMPT
    pth = uconst.Defaults.PTH
    err_report = lambda key: ugen.err_Q(
        f"Invalid type for config option '{key}'; using default value"
    )

    cfg = sandbox_runpy(uconst.CFG_FL)
    if cfg is None:
        return Cfg(prompt=prompt, pth=pth)

    for key in cfg:
        val = cfg[key]

        # Only callables and strings are allowed for prompts
        if key == "PROMPT":
            if not (isinstance(val, str) or callable(val)):
                err_report(key)
                continue
            prompt = val
        # Only a tuple of strings are allowed for the path variable
        elif key == "PTH":
            if not isinstance(val, tuple):
                err_report(key)
                continue
            for i in val:
                if not isinstance(i, str):
                    err_report(key)
                    continue
            pth = val

    return Cfg(prompt=prompt, pth=pth)
