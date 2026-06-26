from string import Template
import re
from typing import Optional

from bs4 import Tag

from .exceptions import ParsingException

MARKDOWN_EXT = ".md"


class MarkdownFormatter:
    """Collection of functions for converting
    [BeautifulSoup `Tag`](https://beautiful-soup-4.readthedocs.io/en/latest/#tag)
    to markdown strings.

    """

    _templates = {"code": Template("```${language}\n${content}\n```")}

    def __init__(self, target_language: Optional[str] = None):

        if target_language is None:
            target_language = ""
        self._target_language = target_language

    def convert_tag(self, tag: Tag) -> str:
        """Convert `Tag` to markdown string."""

        tag_type = type(tag).__name__

        if tag_type == "Tag":
            tag_type = tag.name

        match type(tag).__name__:
            case re.match(r"h\d+", tag_type):
                func = self.header
            case "comment":
                func = self.comment
            case "code":
                func = self.code
            case "p":
                func = self.paragraph
            case "navigablestring":
                func = lambda s: s
            case _:
                raise ParsingException(f"No format function for '{tag_type}' tag")

        return func(tag)

    @staticmethod
    def make_md_head(title: str, level: int) -> str:
        """Make markdown header string."""
        return f"{'#' * level} {title}"

    def code(self, code_tag: Tag) -> str:
        """See `code_block`."""

        return self.code_block(code_tag, target_language=self._target_language)

    @classmethod
    def code_block(cls, code_tag: Tag, target_language: str) -> str:
        """
        Make md code block from `<code>` tag.

        The target language must be provided, but can be empty string.
        """

        template = cls._templates["code"]

        try:
            content = code_tag.pre.string
        except AttributeError as exc:
            raise ParsingException(f"Could not get content of 'pre' tag in:\n{code_tag}") from exc

        language_lst = code_tag["class"]
        if len(language_lst) == 0:
            raise ParsingException(f"No code language class in\n{code_tag}")
        elif len(language_lst) > 1:
            raise ParsingException(
                f"Multiple classes in tag; cannot determine code language\n{code_tag}"
            )

        match language_lst[0]:
            # see https://github.com/swig/swig/blob/master/Doc/Manual/README
            case "code":
                language = "swig"
            case "shell":
                language = "shell"
            case "targetlang":
                language = target_language
            case "diagram":
                language = ""

        return template.substitute(language=language, content=content)

    @classmethod
    def header(cls, header_tag: Tag) -> str:
        """Make markdown header string."""

        if header_tag.a is not None:
            title = header_tag.a.string
            attrs = header_tag.a.attrs
            anchor = " " + " ".join([f'{key}="{value}"' for key, value in attrs.items()])
            a = f"<a{anchor}></a> "
        else:
            title = header_tag.string
            a = ""

        if (m := re.match(r"h(?P<level>\d+)", header_tag.name)) is not None:
            header_level = int(m.group("level"))
        else:
            raise ParsingException(f"Cannot get header level from '{header_tag.name}'")

        return cls.make_md_head(f"{a}{title}", header_level)

    @staticmethod
    def comment(comment_tag: Tag) -> str:
        """Make comment string."""

        return f"<!--{comment_tag.string}-->"

    @staticmethod
    def paragraph(p_tag: Tag) -> str:
        """Make paragraph string."""
        return p_tag.string