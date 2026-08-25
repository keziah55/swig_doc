#!/usr/bin/env python3
"""
Convert SWIG html Manual to markdown.
"""

from pathlib import Path
from swig_doc import SwigMarkdownGenerator


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

    swig_refs = ["master", "v4.5.0", "v4.4.1"]

    if args.swig_path is not None:
        swig_path = args.swig_path.absolute()
    else:
        swig_path = None

    md_generator = SwigMarkdownGenerator(swig_path)
    md_generator.make_swig_markdown(swig_refs)
