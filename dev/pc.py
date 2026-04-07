import logging as lg
import os
import shutil as sh
import subprocess as sp
import sys
import typing as ty

ANSI_RESET = "\x1b[0m"
ANSI_GREEN_4 = "\x1b[92m"
called_nm = os.path.basename(sys.argv[0])
lgr = lg.getLogger(__name__)
lg.basicConfig(
    format=f"{ANSI_GREEN_4}{called_nm}:{ANSI_RESET} %(message)s",
    level=lg.INFO
)


class Cfg(ty.NamedTuple):
    no_docstrs: bool
    lto: bool
    keep_tmp: bool
    rm_pyi: bool
    quiet: bool
    show_mods: bool
    run: bool
    build_dir: str | None
    out_fl_nm: str | None
    args: list[str]


def parse_args() -> Cfg:
    no_docstrs = True
    lto = False
    keep_tmp = True
    rm_pyi = True
    quiet = True
    show_mods = False
    run = False
    build_dir = None
    out_fl_nm = None
    args = []

    toks = sys.argv[1 :]
    len_toks = len(toks)
    parse_opts_flags = True
    skip = 0

    for i, tok in enumerate(toks):
        if skip:
            skip -= 1
            continue
        if not parse_opts_flags:
            args.append(tok)

        if tok in ("-h", "--help"):
            print("See the source, fuckass")
            sys.exit(1)
        if tok in ("-r", "--run"):
            run = True
        elif tok in ("-lto", "--enable-lto"):
            lto = True
        elif tok in ("-ds", "--no-docstrings"):
            no_docstrs = False
        elif tok in ("-pyi", "--keep-pyi-file"):
            rm_pyi = False
        elif tok in ("-rtd", "--remove-tmp-dir"):
            keep_tmp = False
        elif tok in ("-Q", "--no-quiet"):
            quiet = False
        elif tok in ("-sm", "--show-modules"):
            show_mods = True
        elif tok in ("-bd", "--build-dir"):
            if i == len_toks - 1:
                sys.stderr.write(f"{called_nm}: Expected value for option '{tok}'\n")
                sys.exit(1)
            build_dir = toks[i + 1]
            skip = 1
        elif tok in ("-of", "--output-filename"):
            if i == len_toks - 1:
                sys.stderr.write(f"{called_nm}: Expected value for option '{tok}'\n")
                sys.exit(1)
            out_fl_nm = toks[i + 1]
            skip = 1
        elif tok == "--":
            parse_opts_flags = False
        else:
            args.append(tok)

    min_num_of_args = 1
    max_num_of_args = 1
    if len(args) < min_num_of_args:
        sys.stderr.write(
            f"{called_nm}: Insufficient arguments; expected at least {min_num_of_args}, got {len(args)}\n"
        )
        sys.exit(2)
    elif len(args) > max_num_of_args:
        sys.stderr.write(
            f"{called_nm}: Unexpected arguments; expected at most {max_num_of_args}, got {len(args)}\n"
        )
        sys.exit(2)

    return Cfg(
        no_docstrs=no_docstrs,
        lto=lto,
        keep_tmp=keep_tmp,
        rm_pyi=rm_pyi,
        quiet=quiet,
        show_mods=show_mods,
        run=run,
        build_dir=build_dir,
        out_fl_nm=out_fl_nm,
        args=args
    )


def main() -> None:
    cfg = parse_args()

    lgr.info(f"Using Python at {sys.executable}")
    fl = cfg.args[0]
    base_nm = os.path.splitext(os.path.basename(fl))[0]
    proj_root_dir = os.path.dirname(os.path.dirname(fl))
    build_dir = ("build" if cfg.build_dir is None else cfg.build_dir)
    out_fl_nm = (base_nm if cfg.out_fl_nm is None else cfg.out_fl_nm)
    build_dir_pth = os.path.join(proj_root_dir, build_dir)
    tmp_dir_pth = os.path.join(proj_root_dir, "tmp")
    bin_dir_pth = os.path.join(proj_root_dir, "src", "bin")
    cfg_fl_pth = os.path.join(proj_root_dir, "src", "cfg.py")

    cmd = [
        "python",
        "-m",
        "nuitka",
        "--mode=standalone",
        "--follow-imports",
        "--python-flag=no_docstrings" if cfg.no_docstrs else "",
        "--lto=yes" if cfg.lto else "--lto=no",
        "--run" if cfg.run else "",
        "--remove-output" if not cfg.keep_tmp else "",
        "--no-pyi-file" if cfg.rm_pyi else "",
        "--quiet" if cfg.quiet else "",
        "--show-modules" if cfg.show_mods else "",
        "--include-package=intrpr.builtin_cmds",
        f"--output-folder-name={build_dir}",
        f"--output-dir={proj_root_dir}",
        f"--output-filename={out_fl_nm}",
        cfg.args[0]
    ]

    sh.rmtree(build_dir_pth, ignore_errors=True)
    lgr.info(f"Removed build directory")
    sh.rmtree(tmp_dir_pth, ignore_errors=True)
    lgr.info(f"Removed tmp directory")
    compld_proc = sp.run(
        [i for i in cmd if i],
        text=True,
        capture_output=False
    )

    if compld_proc.returncode == 0:
        if cfg.keep_tmp:
            sh.move(
                os.path.join(proj_root_dir, "build.build"),
                tmp_dir_pth
            )
            lgr.info(f"Moved build.build to tmp")
        sh.move(
            os.path.join(proj_root_dir, build_dir + ".dist"),
            build_dir_pth
        )
        lgr.info(f"Moved {build_dir}.dist to {build_dir}")
        sh.copytree(bin_dir_pth, os.path.join(build_dir_pth, "bin"))
        lgr.info(f"Copied bin to build directory")
        sh.copy2(cfg_fl_pth, build_dir_pth)
        lgr.info(f"Copied config to build directory")


if __name__ == "__main__":
    main()
