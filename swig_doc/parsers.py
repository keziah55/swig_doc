from dataclasses import dataclass
from pathlib import Path
import html
from typing import Optional
import re

from bs4 import BeautifulSoup

from .md_utils import MARKDOWN_EXT, MarkdownFormatter
from .exceptions import ParsingException


@dataclass
class PageSection:

    title: str
    level: int
    anchor: str

    def make_md(self) -> str:
        """Make all markdown for this section."""

        s = self.make_md_head()

        return s

    def make_md_head(self) -> str:
        """Make markdown header string."""
        return MarkdownFormatter.make_md_head(self.title, self.level)


class HtmlPageParser:
    """
    Class to parse a page of html.

    Parameters
    ----------
    html_file
        File to parse.
    target_language
        Language that is the subject of this html page. Pass `None` if there is no
        target language.
    """

    def __init__(self, html_file: Path, target_language: Optional[str] = None):

        html_text = html_file.read_text()
        self._soup = BeautifulSoup(html_text, "html.parser")

        self._sections = []

        self._md_formatter = MarkdownFormatter(target_language=target_language)

    def parse(self) -> str:
        """Parse html and generate string of markdown."""

        elements = self._walk()
        text = "".join(elements)

        text = re.sub(r"\n +", "\n", text)
        text = MarkdownFormatter.convert_text_format(text)

        # convert html entities into unicode
        text = html.unescape(text)

        return text

    def _walk(self) -> list[str]:

        elements = []

        item = self._soup.body.contents[0]

        while item is not None:
            if item.name == "div" and "sectiontoc" in item["class"]:
                item = item.next_sibling
                continue

            try:
                s = self._md_formatter.convert_tag(item)
            except ParsingException:
                # print("####")
                # print(item)
                # print(err)
                # print("####")
                item = item.next_element
            else:
                # print("----")
                # print(item)
                # print(s)
                # print("----")

                elements.append(s)
                item = item.next_sibling

        # for item in self._soup.body:
        #     if item.name == "div" and "sectiontoc" in item["class"]:
        #         continue
        #     else:
        #         elements.append(self._md_formatter.convert_tag(item))

        return elements


class SwigDocParser:
    """
    Parse directory of SWIG Manual pages and create markdown equivalents.

    Parameters
    ----------
    html_path
        `swig/Doc/Manual` path.
    out_path
        Directory to write markdown to.
    """

    def __init__(self, html_path: Path, out_path: Path):

        if not html_path.exists() or not html_path.is_dir():
            raise FileNotFoundError(f"No such directory '{html_path}'")

        self._html_path = html_path

        self._out_path = out_path
        self._out_path.mkdir(parents=True, exist_ok=True)

        self._chapters = self._get_chapters_list()

    def write(self):
        """Write all files."""

        self._write_index()

        for name in self._chapters:
            self._write_file(name)

    def _get_chapters_list(self) -> list[str]:

        file = self._html_path.joinpath("chapters")
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(f"No such 'chapters' file '{file}'")

        chapters = [f"{Path(s.strip()).stem}" for s in file.read_text().split("\n") if s]

        return chapters

    def _write_index(self):
        """Write `index.md` page listing all pages."""

        index_file = self._out_path.joinpath(f"index{MARKDOWN_EXT}")

        lines = [MarkdownFormatter.make_md_head("SWIG", 1)]
        lines += [f"- [{name}]({name}{MARKDOWN_EXT})" for name in self._chapters]

        index_file.write_text("\n".join(lines))

    def _write_file(self, name: str):
        """Write markdown file from html page for the given name."""

        html_file = self._html_path.joinpath(f"{name}.html")

        if not html_file.exists():
            # for now
            return

        parser = HtmlPageParser(html_file)
        text = parser.parse()

        out_file = self._out_path.joinpath(f"{name}{MARKDOWN_EXT}")

        out_file.write_text(text)
