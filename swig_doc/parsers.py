from pathlib import Path
from typing import Optional

from .html_parser import HtmlPageParser
from .md_utils import MARKDOWN_EXT, make_md_head

# from .exceptions import ParsingException

# TODO: make zensical.toml nav from chapters


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

        self._languages = [
            "android",
            "cplusplus11",
            "cplusplus14",
            "cplusplus17",
            "cplusplus20",
            "csharp",
            "d",
            "go",
            "guile",
            "java",
            "javascript",
            "lua",
            "octave",
            "perl5",
            "php",
            "python",
            "r",
            "ruby",
            "scilab",
            "tcl",
            "c",
            "ocaml",
        ]

        self._language_lookup = {"android": "java", "cplusplus": "c++", "csharp": "c#"}

    def write(self):
        """Write all files."""

        self._write_index()

        for name in self._chapters:
            # if name != "Python":
            # continue
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

        lines = [make_md_head("SWIG", 1)]
        lines += [f"- [{name}]({name}{MARKDOWN_EXT})" for name in self._chapters]

        index_file.write_text("\n".join(lines))

    def _write_file(self, name: str):
        """Write markdown file from html page for the given name."""

        html_file = self._html_path.joinpath(f"{name}.html")

        if not html_file.exists():
            # for now
            return

        print()
        print(name)
        language = self._get_target_language(name)
        parser = HtmlPageParser(target_language=language)
        text = parser.parse(html_file)

        out_file = self._out_path.joinpath(f"{name}{MARKDOWN_EXT}")

        out_file.write_text(text)

    def _get_target_language(self, name: str) -> Optional[str]:
        """Get target language for chapter."""

        name = name.lower()
        if name in self._languages:
            return self._language_lookup.get(name, name)
        else:
            return None
