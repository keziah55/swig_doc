#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
import re

from bs4 import BeautifulSoup


_MARKDOWN_EXT = ".md"


def _make_md_head(title: str, level: int) -> str:
    """Make markdown header string."""
    return f"{'#' * level} {title}"


@dataclass
class PageSection:

    title: str
    level: int
    anchor: str

    def make_md(self) -> str:
        """Make all markdown for this section."""

        s = self._make_md_head()

        return s

    def _make_md_head(self) -> str:
        """Make markdown header string."""
        return _make_md_head(self.title, self.level)


class HtmlPageParser:
    """
    Class to parse a page of html.

    Parameters
    ----------
    html_file
        File to parse.
    """

    def __init__(self, html_file: Path):

        html_text = html_file.read_text()
        self._soup = BeautifulSoup(html_text, "html.parser")

        self._sections = []

    def parse(self) -> str:
        """Parse html and generate string of markdown."""

        for tag in self._soup.find_all("h1"):
            self._sections.append(PageSection(title=tag.string, level=1, anchor=tag.a["name"]))

        text = "\n".join([section.make_md() for section in self._sections])

        return text


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

        index_file = self._out_path.joinpath(f"index{_MARKDOWN_EXT}")

        lines = [_make_md_head("SWIG", 1)]
        lines += [f"- [{name}]({name}{_MARKDOWN_EXT})" for name in self._chapters]

        index_file.write_text("\n".join(lines))

    def _write_file(self, name: str):
        """Write markdown file from html page for the given name."""

        html_file = self._html_path.joinpath(f"{name}.html")

        if not html_file.exists():
            # for now
            return

        parser = HtmlPageParser(html_file)
        text = parser.parse()

        out_file = self._out_path.joinpath(f"{name}{_MARKDOWN_EXT}")

        out_file.write_text(text)


if __name__ == "__main__":

    repo_root = Path(__file__).parents[1]

    # html_file = repo_root.parent.joinpath("swig", "Doc", "Manual", "Python.html")
    html_path = repo_root.joinpath("tmp_data", "Manual")
    out_path = repo_root.joinpath("docs")

    swig_doc_parser = SwigDocParser(html_path, out_path)
    swig_doc_parser.write()
