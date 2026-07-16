import re
from typing import Optional, Literal, Callable
from functools import partial

from .tag_stack import TagStackItem
from .exceptions import ParsingException

MARKDOWN_EXT = ".md"

HEADER_REGEX = re.compile(r"h(?P<level>\d+)")

def make_md_head(title: str, level: int, custom_id: Optional[str] = None) -> str:
    """Make markdown header string."""

    if custom_id is not None:
        custom_id = f" {{{custom_id}}}"
    else:
        custom_id = ""

    return f"{'#' * level} {title}{custom_id}"


class HtmlToMd:
    """
    Class or static/classmethods to return markdown elements for html tags.

    Use `get` to get the function for a given tag.
    """

    _TARGET_LANGUAGE = ""
    """Target programming language to use for code blocks."""

    @classmethod
    def set_target_language(cls, target_language: str):
        cls._TARGET_LANGUAGE = target_language

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
    def pre(cls, mode: Literal["start", "end"], parent: Optional[TagStackItem] = None) -> str:
        """Handle code block, using `parent` to get language."""

        match mode:
            case "start":
                if parent is not None and (code_type := parent.attrs.get("class", "")):
                    if code_type == "targetlang":
                        code_type = cls._TARGET_LANGUAGE
                    return f"```{code_type}\n"

            case "end":
                return "\n```"

    @staticmethod
    def title(mode: Literal["start", "end"], **kwargs) -> str:
        """Handle title tag."""

        match mode:
            case "start":
                return "% "
            case "end":
                return "\n"

    @staticmethod
    def li(mode: Literal["start", "end"], parent: Optional[TagStackItem] = None) -> str:
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
                return ""
            case "end":
                return "\n"

    @classmethod
    def ul(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._list(mode, **kwargs)

    @classmethod
    def ol(cls, mode: Literal["start", "end"], **kwargs) -> str:
        return cls._list(mode, **kwargs)

    @staticmethod
    def tt(*args, **kwargs) -> str:
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
