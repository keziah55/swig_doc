from pathlib import Path
import shutil
import sys
import re

from .swig_doc_parser import SwigDocParser
from .md_utils import make_md_head
from .utils import MARKDOWN_EXT


class SwigMarkdownGenerator:
    """
    Class to create markdown for multiple directories of SWIG docs.

    Also updates `zensical.toml`.

    Call `make_swig_markdown` with paths to SWIG dirs, then can use `zensical build` to
    create the site.
    """

    def __init__(self, repo_root: Path):

        self._docs_path = self._make_docs_path(repo_root)
        self._zensical_toml = repo_root.joinpath("zensical.toml")
        self._default_index_page = "Preface"

    @staticmethod
    def _make_docs_path(repo_root: Path) -> Path:
        """Remove any existing data from `docs` dir."""

        docs_path = repo_root.joinpath("docs")
        if not docs_path.exists():
            raise FileNotFoundError(f"`docs` path not found: '{docs_path}'")

        dont_delete = ["image"]

        for item in docs_path.iterdir():
            if item.name in dont_delete:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            elif item.is_file():
                item.unlink()

        return docs_path

    def make_swig_markdown(self, swig_paths: list[Path]):
        """
        Make markdown pages for all SWIG dirs in `swig_paths`.

        Also write `nav` section in `zensical.toml` file.
        """

        nav = []
        out_paths = []

        for swig_path in swig_paths:

            version_dir = swig_path.name
            out_name = self._make_outdir_name(version_dir)
            out_path = self._docs_path.joinpath(out_name)

            print(f"\nRunning SWIG doc parser with Python {sys.version} for SWIG {version_dir}")

            index_list = self._make_swig_markdown(swig_path, out_path)
            out_paths.append(out_path)

            nav += self._make_nav_group(
                version_dir, index_list=[p.relative_to(self._docs_path) for p in index_list]
            )

        index_file = self._write_index([p.name for p in out_paths])
        nav.insert(0, f'"{index_file.relative_to(self._docs_path)}",')

        self._write_zensical_nav(nav)

    def _make_swig_markdown(self, swig_path: Path, out_path: Path) -> list[Path]:
        """
        Translate html into markdown for given dir of SWIG docs.

        Return list of markdown paths from `SwigDocParser`.
        """

        if not swig_path.exists():
            raise FileNotFoundError(f"SWIG path not found: {swig_path}")

        html_path = swig_path.joinpath("Doc", "Manual")

        swig_doc_parser = SwigDocParser(html_path, out_path)
        swig_doc_parser.write(validate=True)

        return swig_doc_parser.index_list

    @staticmethod
    def _make_outdir_name(tag: str) -> str:
        """Convert tag to url part."""

        if tag == "latest":
            return tag

        if (m := re.match(r"v(?P<major_minor>\d+\.\d+)\.\d+", tag)) is not None:
            return f"Doc{m.group("major_minor")}"

        raise ValueError(f"Cannot convert '{tag}' to url slug")

    @staticmethod
    def _make_nav_group(version: str, index_list: list[str]) -> list[str]:
        """Make toml array of names from `index_list`."""

        indent = " " * 4
        s = [f'{{ "{version}" = [']
        s += [f'{indent}"{name}", ' for name in index_list]
        s.append("] },")

        return s

    def _write_zensical_nav(self, nav_groups: list[str]):
        """Update `nav` section in `zensical.toml`."""

        indent = " " * 4
        nav = indent + f"\n{indent}".join(nav_groups)

        zensical_toml = self._zensical_toml.read_text()

        m = re.search(r"nav = \[\n(?P<content>.*)\n\]", zensical_toml, flags=re.DOTALL)
        if m is None:
            raise Exception("Could not find `nav` section in zensical.toml")

        idx0, idx1 = m.span("content")
        text = zensical_toml[:idx0] + nav + zensical_toml[idx1:]

        self._zensical_toml.write_text(text)

    def _write_index(self, doc_versions: list[str]) -> Path:
        """Write `index.md` file with links to all doc versions."""

        # Note: passing in `doc_versions` list rather than `self_docs_path.iterdir()`
        # because we want to list them in the order they were generated

        index_file = self._docs_path.joinpath(f"index{MARKDOWN_EXT}")

        lines = [make_md_head("SWIG Manual", 1), ""]
        lines += [
            f"- [{name}]({name}/{self._default_index_page}{MARKDOWN_EXT})"
            for name in doc_versions
        ]

        index_file.write_text("\n".join(lines))

        return index_file
