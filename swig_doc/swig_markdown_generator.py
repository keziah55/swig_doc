from pathlib import Path
import shutil
import sys
import re
import tempfile
import subprocess
import os
from typing import Optional

from .swig_doc_parser import SwigDocParser
from .md_utils import make_md_head
from .utils import MARKDOWN_EXT


class GitManager:
    """
    Class to manage checking out tags from SWIG git repo.

    Note this is intended to be used as a context manager, ike so:
    ```
    with GitManager(*args) as git_manager:
        ...
    ```

    If you do not wish to use it as a context manager, you will have to call `setup()` and
    `clean()` at the beginning and end of use.
    """

    def __init__(
        self,
        target_dir: Optional[Path] = None,
        repo_url: str = "https://github.com/swig/swig.git",
    ):

        self._target_dir = target_dir
        self._repo_url = repo_url

    def setup(self):
        self._using_tmp = False

        # we'll need to chdir into target_dir, so store cwd so we can restore when done
        self._cwd = Path.cwd()

        if self._target_dir is None:
            target_dir = Path(tempfile.mkdtemp(prefix="swig_doc_"))
            self._git_repo_command_static(target_dir, self._cwd, "clone", self._repo_url)
            self._using_tmp = True
            self._target_dir = target_dir
        else:
            # check that given target_dir is swig repo
            self._verify_git_repo(self._target_dir)

        self._orig_branch = self._get_git_branch()

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clean()

    @property
    def repo_path(self) -> Optional[Path]:
        """Return path to repo."""

        return self._target_dir

    def checkout(self, ref: str):
        """Checkout branch or tag."""

        self._git_repo_command("checkout", ref)

    @classmethod
    def _git_repo_command_static(cls, repo_dir: Path, cwd: Path, cmd: str, *args):

        ret_val = None
        err_msg = None

        os.chdir(repo_dir)
        ret_val, err_msg = cls._git_command(cmd, *args)
        os.chdir(cwd)

        if err_msg is not None:
            arg_str = f' {" ".join(args)} ' if args else ""
            raise Exception(f"git {cmd}{arg_str}failed with error '{err_msg}'")

        return ret_val

    @staticmethod
    def _git_command(cmd: str, *args) -> tuple[Optional[str], Optional[str]]:
        """Execute git command in current working dir and return stdout and stderr."""

        err_msg = None
        ret_val = None

        try:
            p = subprocess.run(["git", cmd, *args], capture_output=True)
        except Exception as err:
            err_msg = str(err)
        else:
            if p.returncode != 0:
                err_msg = p.stderr.decode()
            else:
                ret_val = p.stdout.decode()

        return ret_val, err_msg

    def _git_repo_command(self, cmd: str, *args) -> str:
        """Chdir to git repo dir and run `git <cmd> <args>`"""

        return self._git_repo_command_static(self._target_dir, self._cwd, cmd, *args)

    @staticmethod
    def _verify_git_repo(repo_path: Path):
        """Raise exception if `repo_path` is not a git repo."""

        if not repo_path.joinpath(".git").exists():
            raise Exception(f"'{repo_path}' is not a git repository")

    def clean(self):
        """Remove temporary directory or return to original git branch."""

        if self._using_tmp:
            shutil.rmtree(self._target_dir)
        else:
            self.checkout(self._orig_branch)

    def _git_clone(self, target_dir: Path, repo_url: str):
        """Clone git repo to `target_dir`."""

        self._git_repo_command("clone", repo_url, str(target_dir))

    def _get_git_branch(self) -> str:
        """Return current gi branch name."""

        git_branch_info = self._git_repo_command("branch")

        if (
            m := re.search(
                r"^ *\* +(?P<prefix>\(HEAD detached at )?(?P<branch_name>\S+)(?(prefix)\))",
                git_branch_info,
                flags=re.MULTILINE,
            )
        ) is not None:
            return m.group("branch_name")
        else:
            raise Exception(f"Could not parse git branch info from:\n{git_branch_info}")


class SwigMarkdownGenerator:
    """
    Class to create markdown for multiple directories of SWIG docs.

    Also updates `zensical.toml`.

    Call `make_swig_markdown` with paths to SWIG dirs, then can use `zensical build` to
    create the site.
    """

    def __init__(self, repo_path: Optional[Path] = None):

        self._repo_path = repo_path

        out_path = Path(__file__).parents[1]

        self._zensical_toml = out_path.joinpath("zensical.toml")
        self._docs_path = self._make_docs_path(out_path)

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

    def make_swig_markdown(self, swig_refs: list[str]):
        """
        Make markdown pages for all in `docs_mapping`.

        Also write `nav` section in `zensical.toml` file.

        Parameters
        ----------
        swig_refs
            List of branch/tag names to checkout.
        """

        nav = []
        out_paths = []

        with GitManager(target_dir=self._repo_path) as git_manager:

            for ref in swig_refs:

                git_manager.checkout(ref)

                out_name = self._make_outdir_name(ref)
                out_path = self._docs_path.joinpath(out_name)

                print(f"\nRunning SWIG doc parser with Python {sys.version} for SWIG '{ref}'")

                index_list = self._make_swig_markdown(git_manager.repo_path, out_path)
                out_paths.append(out_path)

                nav += self._make_nav_group(
                    out_name, index_list=[p.relative_to(self._docs_path) for p in index_list]
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

        if tag == "master":
            return "latest"

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
