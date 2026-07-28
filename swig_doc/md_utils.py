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


class HtmlToMd:
    """
    Class or static/classmethods to return markdown elements for html tags.

    Use `get` to get the function for a given tag.
    """

    _TARGET_LANGUAGE = ""
    """Target programming language to use for code blocks."""

    _SHELL_LANGUAGE = "shell"
    """Target shell language for code blocks."""

    @classmethod
    def set_target_language(cls, target_language: Optional[str]):
        """Set language to use for 'targetlang' code blocks."""

        if target_language is None:
            target_language = ""
        cls._TARGET_LANGUAGE = target_language

    @classmethod
    def set_shell_language(cls, shell_language: Optional[str]):
        """Set language to use fo 'shell' code blocks."""

        if shell_language is None:
            shell_language = "shell"
        cls._SHELL_LANGUAGE = shell_language

    @classmethod
    def get(cls, name: str) -> Callable:
        """Get function to handle `name` html tag."""

        if (m := HEADER_REGEX.match(name)) is not None:
            return partial(cls.h, int(m.group("level")))

        if (func := getattr(cls, name, None)) is None:
            return None
        return func

    @classmethod
    def h(cls, header_level: int, mode: Literal["start", "end"], **kwargs) -> str:
        """Make markdown header string."""

        match mode:
            case "start":
                return f"\n{'#' * header_level} "
            case "end":
                return "\n"

    @staticmethod
    def p(mode: Literal["start", "end", "data"], data: str = "", **kwargs) -> str:
        """Handle paragraph tag."""

        match mode:
            case "start":
                return "\n"
            case "end":
                return ""
            case "data":
                return re.sub(r"\n +", "\n", data)

    @classmethod
    def pre(cls, mode: Literal["start", "end"], parent: Optional[DocumentItem] = None) -> str:
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
                code_type = cls._TARGET_LANGUAGE
            elif "shell" in code_types:
                code_type = cls._SHELL_LANGUAGE
            elif "code" in code_types:
                code_type = "swig"

        match mode:
            case "start":
                return f"{symbol}{code_type}{new_line}"

            case "end":
                return f"{new_line}{symbol}"

    @staticmethod
    def title(mode: Literal["start", "end"], **kwargs) -> str:
        """Handle title tag."""

        match mode:
            case "start":
                return ""
            case "end":
                return "\n===="

    @staticmethod
    def li(mode: Literal["start", "end"], parent: Optional[DocumentItem] = None) -> str:
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

    @classmethod
    def ul(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._list(mode, **kwargs)

    @classmethod
    def ol(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._list(mode, **kwargs)

    @classmethod
    def dl(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._list(mode, **kwargs)

    @staticmethod
    def tt(*args, **kwargs) -> str:
        return "`"

    @staticmethod
    def code(*args, **kwargs) -> str:
        return "`"

    @staticmethod
    def em(*args, **kwargs) -> str:
        return "*"

    @staticmethod
    def i(*args, **kwargs) -> str:
        return "*"

    @staticmethod
    def strong(*args, **kwargs) -> str:
        """Handle <strong> tag (bold)."""
        return "**"

    @staticmethod
    def b(*args, **kwargs) -> str:
        """Handle <b> tag (bold)."""
        return "**"

    @staticmethod
    def s(*args, **kwargs) -> str:
        """Handle <s> tag (strikethrough)."""
        return "~~"

    @staticmethod
    def sub(*args, **kwargs) -> str:
        """Handle <sub> tag (subscript)."""
        return "~"

    @staticmethod
    def sup(*args, **kwargs) -> str:
        """Handle <sup> tag (superscript)."""
        return "^"

    @staticmethod
    def mark(*args, **kwargs) -> str:
        """Handle <mark> tag (highlight)."""
        return "=="

    @staticmethod
    def q(*args, **kwargs) -> str:
        """Handle <q> tag (quote marks)."""
        return '"'

    @staticmethod
    def hr(*args, **kwargs) -> str:
        """Handle <hr> tag (horizontal line)."""
        return "\n---\n\n"

    @staticmethod
    def br(*args, **kwargs) -> str:
        """Handle <br> tag (new line)."""
        return "\n\n"

    @staticmethod
    def blockquote(mode: Literal["start", "end", "data"], data: str = "", **kwargs) -> str:

        s = "\n> "

        match mode:
            case "start":
                return s
            case "end":
                return ""
            case "data":
                return re.sub(r"\n", s, data)

    @staticmethod
    def table(mode: Literal["start", "end", "data"], **kwargs) -> str:
        match mode:
            case "start":
                return "\n"
            case "end":
                return ""

    @staticmethod
    def tr(mode: Literal["start", "end"], **kwargs) -> str:
        match mode:
            case "start":
                return "| "
            case "end":
                return "\n"

    @classmethod
    def td(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._td(mode, **kwargs)

    @classmethod
    def th(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._td(mode, **kwargs)

    @staticmethod
    def _td(mode: Literal["start", "end"], **kwargs) -> str:
        if mode == "end":
            return " | "
        else:
            return ""

    @staticmethod
    def dt(mode: Literal["start", "end"], **kwargs) -> str:

        match mode:
            case "start":
                return "\n- "
            case "end":
                return "\n\n"

    @staticmethod
    def dd(mode: Literal["start", "end"], **kwargs) -> str:

        match mode:
            case "start" | "data":
                return ""
            case "end":
                return "\n\n"
