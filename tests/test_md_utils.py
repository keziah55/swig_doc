import json

from bs4 import BeautifulSoup

from swig_doc.md_utils import MarkdownFormatter
from swig_doc.exceptions import ParsingException

import pytest
from .conftest import MockTag


@pytest.mark.parametrize("code_type", ["targetlang", "code", "shell", "diagram"])
def test_code_block(data_dir, code_type):

    html = data_dir.joinpath("code_blocks.html").read_text()

    with open(data_dir.joinpath("code_blocks_md.json")) as fileobj:
        md = json.load(fileobj)

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("div", attrs={"class_": code_type}):
        expected = md[code_type]
        assert MarkdownFormatter.code_block(tag, target_language="python") == expected


@pytest.mark.parametrize(
    "tag,err_msg",
    [
        (MockTag("div"), r"Could not get content of 'pre' tag in:\n<div></div>"),
        (
            MockTag("div", attrs={"class": ["a", "b"]}, children=[MockTag("pre", text="demo")]),
            r"Multiple classes in tag; cannot determine code language",
        ),
        (
            MockTag("div", attrs={"class": []}, children=[MockTag("pre", text="demo")]),
            r"No code language class in",
        ),
    ],
)
def test_code_block_error(tag, err_msg):

    with pytest.raises(ParsingException, match=err_msg):
        MarkdownFormatter.code_block(tag, target_language="python")


def test_make_md_head():
    assert MarkdownFormatter.make_md_head("Heading", level=4) == "#### Heading"


@pytest.mark.parametrize(
    "tag, expected",
    [
        (
            MockTag("h4", children=[MockTag("a", attrs={"name": "Python"}, text="Python")]),
            '#### <a name="Python"></a> Python',
        ),
        (
            MockTag("h1", text="Python"),
            "# Python",
        ),
    ],
)
def test_header(tag, expected):

    assert MarkdownFormatter.header(tag) == expected


def test_header_error():

    tag = MockTag("h", text="Python")

    with pytest.raises(ParsingException, match=r"Cannot get header level from 'h'"):
        MarkdownFormatter.header(tag)


def test_convert_text_format(data_dir):

    html = data_dir.joinpath("convert_text_format.html").read_text()
    expected = data_dir.joinpath("convert_text_format.md").read_text()

    assert MarkdownFormatter.convert_text_format(html) == expected
