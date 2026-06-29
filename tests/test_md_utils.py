import json

from bs4 import BeautifulSoup

from swig_doc.parsers import HtmlPageParser
from swig_doc.md_utils import MarkdownFormatter
from swig_doc.exceptions import ParsingException

import pytest


@pytest.mark.parametrize("code_type", ["targetlang", "code", "shell", "diagram"])
def test_code_block(data_dir, code_type):

    fname = "code_blocks"

    html = data_dir.joinpath(f"{fname}.html").read_text()

    with open(data_dir.joinpath(f"{fname}.json")) as fileobj:
        md = json.load(fileobj)

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("div", attrs={"class_": code_type}):
        expected = md[code_type]
        assert MarkdownFormatter.code_block(tag, target_language="python") == expected


@pytest.mark.parametrize(
    "html,err_msg",
    [
        ("<div></div>", r"Could not get content of 'pre' tag in:\n<div></div>"),
        (
            '<div class="a b"><pre>demo</pre></div>',
            r"Multiple classes in tag; cannot determine code language",
        ),
        (
            '<div class=""><pre>demo</pre></div>',
            r"No code language class in",
        ),
    ],
)
def test_code_block_error(html, err_msg):

    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("div")

    with pytest.raises(ParsingException, match=err_msg):
        MarkdownFormatter.code_block(tag, target_language="python")


def test_make_md_head():
    assert MarkdownFormatter.make_md_head("Heading", level=4) == "#### Heading"


@pytest.mark.parametrize(
    "html, expected",
    [
        ('<h4><a name="Python">Python</a></h4>', '#### <a name="Python"></a> Python'),
        ("<h1>Python</h1>", "# Python"),
    ],
)
def test_header(html, expected):

    soup = BeautifulSoup(html, "html.parser")
    tag = list(soup.descendants)[0]

    assert MarkdownFormatter.header(tag) == expected


def test_header_error():

    html = "<h>Python<h>"
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("h")

    with pytest.raises(ParsingException, match=r"Cannot get header level from 'h'"):
        MarkdownFormatter.header(tag)


def test_convert_text_format(data_dir):

    fname = "convert_text_format"
    html = data_dir.joinpath(f"{fname}.html").read_text()
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    assert MarkdownFormatter.convert_text_format(html) == expected


def test_html_page_parser(data_dir):

    fname = "paragraphs"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(html_file, target_language="python")

    md = parser.parse()

    print()
    print(md)

    assert md == expected
