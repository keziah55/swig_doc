#!/usr/bin/env python3
"""
Convert SWIG html Manual to markdown.
"""

from pathlib import Path
import tempfile
import subprocess
import shutil

from swig_doc import SwigDocParser


def clone_swig_repo(target_dir: Path):
    swig_url = "https://github.com/swig/swig.git"
    p = subprocess.run(["git", "clone", swig_url, str(target_dir)])

    if p.returncode != 0:
        raise Exception(f"Could not clone SWIG repo: {p.stderr.decode()}")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--swig_path",
        type=Path,
        help=(
            "Path to swig repo root. If not provided, repo will be cloned to a temporary "
            "directory"
        ),
    )
    args = parser.parse_args()

    
    if args.swig_path is None:
        swig_path = Path(tempfile.mkdtemp(prefix="swig_doc_"))
        clone_swig_repo(swig_path)
        using_tmp = True
    else:
        swig_path = args.swig_path
        using_tmp = False

    if not swig_path.exists():
        raise FileNotFoundError(f"SWIG path not found: {swig_path}")

    repo_root = Path(__file__).parent

    html_path = swig_path.joinpath("Doc", "Manual")
    out_path = repo_root.joinpath("docs")

    swig_doc_parser = SwigDocParser(html_path, out_path)
    swig_doc_parser.write()

    if using_tmp:
        # remove temp dir
        shutil.rmtree(swig_path)
