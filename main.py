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
    parser.add_argument(
        "-v",
        "--swig-versions",
        nargs="*",
        help="SWIG branches/tags to build docs for",
        default=["master", "v4.5.0", "v4.4.1", "v4.3.1", "v4.2.1", "v4.1.1", "v4.0.2"],
    )
    args = parser.parse_args()

    if args.swig_path is not None:
        swig_path = args.swig_path.absolute()
    else:
        swig_path = None

    md_generator = SwigMarkdownGenerator(swig_path)
    md_generator.make_swig_markdown(args.swig_versions)
