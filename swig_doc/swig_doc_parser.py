from pathlib import Path
from typing import Optional
import re

from bs4 import BeautifulSoup

from .html_parser import HtmlPageParser
from .md_utils import make_md_head
from .utils import MARKDOWN_EXT, REDIRECT_TEMPLATE


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

        # non-language chapters, where we want to use python the target lang for code blocks
        self._python_chapters = ["arguments", "varargs"]

    def write(self):
        """Write all files."""

        self._write_index()

        validation: dict[str : dict[int, set]] = {}

        for name in self._chapters:
            # if name != "Scilab":
            #     continue
            md = self._make_markdown(name)
            self._write_file(name, md)
            self._write_redirect_page(name)

            if (diff := self._validate(name, md)) is not None:
                validation[name] = diff

        if validation:
            print("The following pages failed header validation:")
            for name, diff in validation.items():
                print(f"{name}:")
                for level, headers in diff.items():
                    print(f"  Header level {level}")
                    for header in headers:
                        print(f"    {header}")

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

    def _make_markdown(self, name: str) -> str:
        """Generate markdown text from html page for the given name."""

        html_file = self._html_path.joinpath(f"{name}.html")

        if not html_file.exists():
            # for now
            return

        print()
        print(name)
        language = self._get_target_language(name)
        shell_language = self._get_shell_language(name)
        parser = HtmlPageParser(target_language=language, shell_language=shell_language)
        text = parser.parse(html_file)

        return text

    def _write_file(self, name: str, text: str):
        """Write markdown file."""

        out_file = self._out_path.joinpath(f"{name}{MARKDOWN_EXT}")
        out_file.write_text(text)

    def _write_redirect_page(self, name: str):
        """Write `[name].html` page that redirects to `base_url/name`."""

        url = f"{name}/"

        html = REDIRECT_TEMPLATE.substitute(url=url)

        out_file = self._out_path.joinpath(f"{name}.html")
        out_file.write_text(html)

    def _get_target_language(self, name: str) -> Optional[str]:
        """Get target language for chapter."""

        name = name.lower()
        if name in self._languages:
            return self._language_lookup.get(name, name)
        elif name in self._python_chapters:
            return "python"
        else:
            return None

    def _get_shell_language(self, name: str) -> Optional[str]:

        name = name.lower()
        if name == "windows":
            # TODO do we actually want/need this? Many of the shell code blocks on the windows
            # page are for mingw/cygwin
            return "powershell"
        return None

    def _validate(self, name: str, md: str) -> Optional[dict[int:set]]:
        """
        Check that headers in html file match those in markdown text.

        Return `None` if there are no differences. Otherwise, return a dict of header level (int)
        and set of non-matching header strings.
        """

        html_file = self._html_path.joinpath(f"{name}.html")
        soup = BeautifulSoup(html_file.read_text(), "html.parser")

        diff = {}

        for header_level in range(1, 7):
            html_headers = [
                (tag.text, tag.a["name"]) for tag in soup.find_all(f"h{header_level}")
            ]

            md_head = f"#{{{header_level}}}"
            md_headers = [
                # un-escape any `>` chars in header string and remove any backticks
                (m.group("h_str").replace("\\>", ">").replace("`", ""), m.group("a_name"))
                for m in re.finditer(
                    r"\n" + md_head + r' <a name="(?P<a_name>\w+)"></a> +(?P<h_str>.+)', md
                )
            ]

            if html_headers != md_headers:
                diff[header_level] = set(html_headers) ^ set(md_headers)

        if diff:
            return diff
        else:
            return None
