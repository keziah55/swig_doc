import re
from typing import Optional, Literal, Callable
from functools import partial

from .doc_item import DocumentItem
from .utils import HEADER_REGEX


def make_md_head(title: str, level: int, custom_id: Optional[str] = None) -> str:
    """Make markdown header string."""

    if custom_id is not None:
        custom_id = f" {{{custom_id}}}"
    else:
        custom_id = ""

    return f"{'#' * level} {title}{custom_id}"


def transform_internal_link(href: str) -> str:
    """
    Internal links point to `[page_name].html`.

    Return with the `.html` removed, retaining any anchor.
    """

    if (
        m := re.match(r"(?P<page_name>\w+)\.html(?P<anchor>\#\w+)?", href)
    ) is not None and re.match(r"https?://", href) is None:
        # NOTE can't use negative lookbehind instead of the second `re.match` there because
        # that requires fixed-length sequence and we want to match against a pattern where
        # the "s" is optional
        href = m.group("page_name")
        if m.group("anchor"):
            href += f"/{m.group("anchor")}"

    return href


def check_parent_skip_fmt(func):
    """
    If parent tag indicates that format tag should be skipped, return "".

    Otherwise call formatting function.
    """

    def inner(self, *args, **kwargs) -> bool:

        parent = kwargs.get("parent", None)

        if parent is not None and parent.tag in self._parent_skip_fmt:
            return ""
        else:
            return func(self, *args, **kwargs)

    return inner


class HtmlToMd:
    """
    Class to return markdown elements for html tags.

    Use `get` to get the function for a given tag.

    Parameters
    ----------
    target_language
        Target programming language to use for code blocks.
    shell_language
        Target shell language for code blocks. Default is "shell".
    """

    def __init__(
        self, target_language: Optional[str] = None, shell_language: Optional[str] = None
    ):

        self._target_language = target_language if target_language is not None else ""
        self._shell_language = shell_language if shell_language is not None else "shell"

        self._parent_skip_fmt = ["pre", "tt", "code"]

    def get(self, name: str) -> Callable:
        """Get function to handle `name` html tag."""

        if (m := HEADER_REGEX.match(name)) is not None:
            return partial(self.h, int(m.group("level")))

        if (func := getattr(self, name, None)) is None:
            return None
        return func

    def h(self, header_level: int, mode: Literal["start", "end"], **kwargs) -> str:
        """Make markdown header string."""

        match mode:
            case "start":
                return f"\n{'#' * header_level} "
            case "end":
                return "\n"

    def p(self, mode: Literal["start", "end", "data"], data: str = "", **kwargs) -> str:
        """Handle paragraph tag."""

        match mode:
            case "start":
                return "\n"
            case "end":
                return ""
            case "data":
                return re.sub(r"\n +", "\n", data)

    def pre(self, mode: Literal["start", "end"], parent: Optional[DocumentItem] = None) -> str:
        """
        Handle code block, using `parent` to get language.

        If `pre` has `div` as parent, use triple back-quote block. Otherwise, use single
        backquote.
        """

        # defaults
        symbol = "`"
        code_type = ""
        new_line = ""

        if parent is not None and parent.tag == "div":
            symbol = "```"
            code_types = parent.attrs.get("class", "").split(" ")
            new_line = "\n"

            if "targetlang" in code_types:
                code_type = self._target_language
            elif "shell" in code_types:
                code_type = self._shell_language
            elif "code" in code_types:
                code_type = "swig"

        match mode:
            case "start":
                return f"{symbol}{code_type}{new_line}"

            case "end":
                return f"{new_line}{symbol}"

    def title(self, mode: Literal["start", "end"], **kwargs) -> str:
        """Handle title tag."""

        match mode:
            case "start":
                return ""
            case "end":
                return "\n===="

    def li(self, mode: Literal["start", "end"], parent: Optional[DocumentItem] = None) -> str:
        """Handle list item tag."""

        match mode:
            case "start":
                match parent.tag:
                    case "ol":
                        return "1. "
                    case _:
                        return "- "
            case "end":
                return ""  # "\n"

    @staticmethod
    def _list(mode: Literal["start", "end"], **kwargs) -> str:
        match mode:
            case "start":
                return "\n"
            case "end":
                return "\n"

    def ul(self, mode: Literal["start", "end"], **kwargs) -> str:
        return self._list(mode, **kwargs)

    def ol(self, mode: Literal["start", "end"], **kwargs) -> str:
        return self._list(mode, **kwargs)

    def dl(self, mode: Literal["start", "end"], **kwargs) -> str:
        return self._list(mode, **kwargs)

    def tt(self, *args, **kwargs) -> str:
        return "`"

    def code(self, *args, **kwargs) -> str:
        return "`"

    @check_parent_skip_fmt
    def em(self, *args, **kwargs) -> str:
        return "*"

    @check_parent_skip_fmt
    def i(self, *args, **kwargs) -> str:
        return "*"

    @check_parent_skip_fmt
    def strong(self, *args, **kwargs) -> str:
        """Handle <strong> tag (bold)."""
        return "**"

    @check_parent_skip_fmt
    def b(self, *args, **kwargs) -> str:
        """Handle <b> tag (bold)."""
        return "**"

    @check_parent_skip_fmt
    def s(self, *args, **kwargs) -> str:
        """Handle <s> tag (strikethrough)."""
        return "~~"

    @check_parent_skip_fmt
    def sub(self, *args, **kwargs) -> str:
        """Handle <sub> tag (subscript)."""
        return "~"

    @check_parent_skip_fmt
    def sup(self, *args, **kwargs) -> str:
        """Handle <sup> tag (superscript)."""
        return "^"

    @check_parent_skip_fmt
    def mark(self, *args, **kwargs) -> str:
        """Handle <mark> tag (highlight)."""
        return "=="

    @check_parent_skip_fmt
    def q(self, *args, **kwargs) -> str:
        """Handle <q> tag (quote marks)."""
        return '"'

    @check_parent_skip_fmt
    def hr(self, *args, **kwargs) -> str:
        """Handle <hr> tag (horizontal line)."""
        return "\n---\n\n"

    def br(self, *args, **kwargs) -> str:
        """Handle <br> tag (new line)."""
        return "\n\n"

    def blockquote(
        self, mode: Literal["start", "end", "data"], data: str = "", **kwargs
    ) -> str:

        s = "\n> "

        match mode:
            case "start":
                return s
            case "end":
                return ""
            case "data":
                return re.sub(r"\n", s, data)

    def table(self, mode: Literal["start", "end", "data"], **kwargs) -> str:
        match mode:
            case "start":
                return "\n"
            case "end":
                return ""

    def tr(self, mode: Literal["start", "end"], **kwargs) -> str:
        match mode:
            case "start":
                return "| "
            case "end":
                return "\n"

    def td(self, mode: Literal["start", "end"], **kwargs) -> str:
        return self._td(mode, **kwargs)

    def th(self, mode: Literal["start", "end"], **kwargs) -> str:
        return self._td(mode, **kwargs)

    @staticmethod
    def _td(mode: Literal["start", "end"], **kwargs) -> str:
        if mode == "end":
            return " | "
        else:
            return ""

    def dt(self, mode: Literal["start", "end"], **kwargs) -> str:

        match mode:
            case "start":
                return "\n- "
            case "end":
                return "\n\n"

    def dd(self, mode: Literal["start", "end"], **kwargs) -> str:

        match mode:
            case "start" | "data":
                return ""
            case "end":
                return "\n\n"
