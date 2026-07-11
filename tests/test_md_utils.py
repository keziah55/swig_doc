import json

from swig_doc.html_parser import HtmlPageParser
from swig_doc.exceptions import ParsingException

import pytest


def test_convert_text_format(data_dir):

    fname = "convert_text_format"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(target_language="python")
    md = parser.parse(html_file)

    print()
    print(md)

    assert md == expected

    # assert MarkdownFormatter.convert_text_format(html) == expected


def test_html_page_parser(data_dir):

    fname = "paragraphs"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(target_language="python")

    md = parser.parse(html_file)

    print()
    print(md)

    assert md == expected
