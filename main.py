#!/usr/bin/env python3
"""
Convert SWIG html Manual to markdown.
"""

from pathlib import Path
import tempfile
import subprocess
import shutil
from typing import Optional


from swig_doc import SwigMarkdownGenerator


def clone_swig_repo(target_dir: Path, tag: Optional[str] = None) -> Path:
    """
    Clone SWIG repo and return path to checked-out code.

    Parameters
    ----------
    target_dir
        Directory to clone to. The source is cloned to a subdir within here; if `tag`
        is provided, that is the subdir name, otherwise "latest".
    tag
        Optionally clone from this tag. If provided, the source code is checked out into
        `<target_dir>/<tag>`.

    Returns
    -------
    Path
        Path to checked out repo.

    Raises
    ------
    Exception
        If `git clone` failed.
    """

    swig_url = "https://github.com/swig/swig.git"
    extra_args = []

    if tag is not None:
        target_dir = target_dir.joinpath(tag)
        extra_args += ["--branch", tag]
    else:
        target_dir = target_dir.joinpath("latest")

    target_dir.mkdir(exist_ok=True, parents=True)

    p = subprocess.run(["git", "clone", swig_url, str(target_dir)] + extra_args)

    if p.returncode != 0:
        raise Exception("Could not clone SWIG repo")

    return target_dir


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

    tmp_path = None
    swig_paths = []

    repo_root = Path(__file__).parent

    if args.swig_path is None:

        tmp_path = Path(tempfile.mkdtemp(prefix="swig_doc_"))

        versions = [None, "v4.5.0", "v4.4.1"]
        for tag in versions:
            clone_path = clone_swig_repo(tmp_path, tag=tag)
            swig_paths.append(clone_path)

    else:
        swig_paths = [p for p in args.swig_path.iterdir() if p.is_dir()]

    md_generator = SwigMarkdownGenerator(repo_root)
    md_generator.make_swig_markdown(swig_paths)

    if tmp_path is not None:
        # remove temp dir
        shutil.rmtree(tmp_path)
