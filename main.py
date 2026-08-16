#!/usr/bin/env python3
"""
Convert SWIG html Manual to markdown.
"""

from pathlib import Path
import tempfile
import subprocess
import shutil
import sys
from typing import Optional
import re

from swig_doc import SwigDocParser
from swig_doc.md_utils import make_md_head
from swig_doc.utils import MARKDOWN_EXT


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


def _make_nav_group(version: str, index_list: list[str]) -> list[str]:
    indent = " " * 4
    s = [f'{{ "{version}" = [']
    s += [f'{indent}"{name}", ' for name in index_list]
    s.append("] },")

    return s


def _write_index(docs_paths: list[Path], default_page: str) -> Path:

    docs_dir = docs_paths[0].parent
    index_file = docs_dir.joinpath(f"index{MARKDOWN_EXT}")

    lines = [make_md_head("SWIG Manual", 1), ""]
    lines += [f"- [{p.name}]({p.name}/{default_page}{MARKDOWN_EXT})" for p in docs_paths]

    index_file.write_text("\n".join(lines))

    return index_file


def _write_zensical_nav(nav: list[str], zensical_file: Path):

    indent = " " * 4
    nav = indent + f"\n{indent}".join(nav)

    zensical_toml = zensical_file.read_text()

    m = re.search(r"nav = \[\n(?P<content>.*)\n\]", zensical_toml, flags=re.DOTALL)
    if m is None:
        raise Exception("Could not find `nav` section in zensical.toml")

    idx0, idx1 = m.span("content")
    text = zensical_toml[:idx0] + nav + zensical_toml[idx1:]

    zensical_file.write_text(text)


def _make_outdir_name(tag: str) -> str:
    """Convert tag to url part."""

    if tag == "latest":
        return tag

    if (m := re.match(r"v(?P<major_minor>\d+\.\d+)\.\d+", tag)) is not None:
        return f"Doc{m.group("major_minor")}"

    raise ValueError(f"Cannot convert '{tag}' to url slug")


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
    docs_path = repo_root.joinpath("docs")
    out_paths = []

    if docs_path.exists():
        shutil.rmtree(docs_path)
    docs_path.mkdir(parents=True)

    nav = []

    if args.swig_path is None:

        tmp_path = Path(tempfile.mkdtemp(prefix="swig_doc_"))

        versions = [None, "v4.5.0", "v4.4.1"]
        for tag in versions:
            clone_path = clone_swig_repo(tmp_path, tag=tag)
            swig_paths.append(clone_path)

    else:
        swig_paths = [p for p in args.swig_path.iterdir() if p.is_dir()]

    for swig_path in swig_paths:

        if not swig_path.exists():
            raise FileNotFoundError(f"SWIG path not found: {swig_path}")

        version_dir = swig_path.name
        out_name = _make_outdir_name(version_dir)

        html_path = swig_path.joinpath("Doc", "Manual")
        out_path = docs_path.joinpath(out_name)
        out_paths.append(out_path)

        print(f"\nRunning SWIG doc parser with Python {sys.version} for SWIG {version_dir}")
        swig_doc_parser = SwigDocParser(html_path, out_path)
        swig_doc_parser.write(validate=True)

        # print(swig_doc_parser.index_list)
        index_list = [p.relative_to(docs_path) for p in swig_doc_parser.index_list]
        nav += _make_nav_group(version_dir, index_list=index_list)

    index_file = _write_index(out_paths, "Preface")
    nav.insert(0, f'"{index_file.relative_to(docs_path)}",')

    _write_zensical_nav(nav, repo_root.joinpath("zensical.toml"))

    if tmp_path is not None:
        # remove temp dir
        shutil.rmtree(tmp_path)
