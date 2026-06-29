#!/usr/bin/env python3

from pathlib import Path

from swig_doc import SwigDocParser



if __name__ == "__main__":

    repo_root = Path(__file__).parent

    html_path = repo_root.joinpath("tmp_data", "Manual")
    out_path = repo_root.joinpath("docs")

    swig_doc_parser = SwigDocParser(html_path, out_path)
    swig_doc_parser.write()
