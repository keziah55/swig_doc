from string import Template
import re
from typing import Optional, Literal

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
    def make_md_head(title: str, level: int, custom_id: Optional[str] = None) -> str:
        """Make markdown header string."""

        if custom_id is not None:
            custom_id = f" {{{custom_id}}}"
        else:
            custom_id = ""

        return f"{'#' * level} {title}{custom_id}"

    @classmethod
    def convert_text_format(cls, html: str) -> str:
        """
        Convert any text formatting tags into markdown.

        Handled tags are:

        | Html                            | Markdown   |
        |---------------------------------|------------|
        | <tt>string</tt>                 | `string`   |
        | <em>string</em>                 | *string*   |
        | <i>string</i>                   | *string*   |
        | <b>string</b>                   | **string** |
        | <strong>string</strong>         | **string** |
        | <s>string</s>                   | ~~string~~ |
        | <sub>string</sub>               | ~string~   |
        | <sup>string</sup>               | ^string^   |
        | <mark>string</mark>             | ==string== |
        | <q>string</q>                   | > string   |
        | <blockquote>string</blockquote> | > string   |
        | <ul><li>string</li></ul>        | - string   |
        | <ol><li>string</li></ol>        | 1. string  |
        | <hr>                            | ---        |

        """

        regexes = [
            (r"<tt>(?P<string>.+?)</tt>", r"`\g<string>`"),
            (r"<em>(?P<string>.+?)</em>", r"*\g<string>*"),
            (r"<i>(?P<string>.+?)</i>", r"*\g<string>*"),
            (r"<b>(?P<string>.+?)</b>", r"**\g<string>**"),
            (r"<strong>(?P<string>.+?)</strong>", r"**\g<string>**"),
            (r"<s>(?P<string>.+?)</s>", r"~~\g<string>~~"),
            (r"<sub>(?P<string>.+?)</sub>", r"~\g<string>~"),
            (r"<sup>(?P<string>.+?)</sup>", r"^\g<string>^"),
            (r"<mark>(?P<string>.+?)</mark>", r"==\g<string>=="),
            (r"<q>(?P<string>.+?)</q>", r'"\g<string>"'),
            (r"<hr>", r"---"),
            (r"<br */>", r"\n\n"),
            (r"<wbr */>", r"\n\n"),
        ]

        for pattern, repl in regexes:
            html = re.sub(pattern, repl, html, flags=re.DOTALL)

        html = cls.convert_lists(html)
        html = cls._convert_blockquote(html)

        return html

    @classmethod
    def convert_lists(cls, html: str) -> str:
        """Convert any ordered or unordered lists in `html` into markdown."""

        for list_type in ["ul", "ol"]:
            html = cls._convert_list(html, list_type)

        return html

    @staticmethod
    def _convert_list(html: str, list_type: Literal["ul", "ol"]) -> str:
        """Convert ordered/unordered lists in `html` into markdown."""

        match list_type:
            case "ul":
                s = r"-"
            case "ol":
                s = r"1."

        regex = re.compile(
            r"(?P<lst><" + list_type + r">(?P<lst_content>.+?)</" + list_type + r">)",
            flags=re.DOTALL,
        )

        while (m := regex.search(html)) is not None:

            list_content = m.group("lst_content")
            list_content = re.sub(
                r"(?P<space>[ \t]*)<li>(?P<item>.+?)</li>",
                s + r" \g<item>",
                list_content,
                flags=re.DOTALL,
            )

            idx0, idx1 = m.span("lst")
            html = html[:idx0] + list_content + html[idx1:]

        return html

    @staticmethod
    def _convert_blockquote(html: str) -> str:
        """Convert html blockquote(s) into markdown."""

        regex = re.compile(
            r"(?P<quote><blockquote>(?P<quote_content>.+?)</blockquote>)", flags=re.DOTALL
        )

        while (m := regex.search(html)) is not None:

            quote_content = m.group("quote_content")
            quote_content = re.sub(r"\n", r"\n> ", quote_content)
            quote_content = "\n> " + quote_content

            idx0, idx1 = m.span("quote")
            html = html[:idx0] + quote_content + html[idx1:]

        return html

    @staticmethod
    def a(tag: Tag) -> str:
        """
        Handle `a` tag.

        `a` can either define a link or an anchor point. This is determined by the attributes;
        `href` (link) or `name` (`anchor`).
        """

        title = tag.string

        try:
            url = tag["href"]
        except KeyError:
            anchor = tag["name"]
            return f'<a> name="{anchor}"</a>'
        else:
            return f"[{title}]({url})"

    def code(self, code_tag: Tag) -> str:
        """See `code_block`."""

        return self.code_block(code_tag, target_language=self._target_language)

    @classmethod
    def code_block(cls, tag: Tag, target_language: str) -> str:
        """
        Make md code block from `<code>` tag.

        The target language must be provided, but can be empty string.
        """

        template = cls._templates["code"]

        try:
            content = tag.pre.string
        except AttributeError as exc:
            raise ParsingException(f"Could not get content of 'pre' tag in:\n{tag}") from exc

        language_lst = tag["class"]
        if len(language_lst) == 0:
            raise ParsingException(f"No code language class in\n{tag}")
        elif len(language_lst) > 1:
            raise ParsingException(
                f"Multiple classes in tag; cannot determine code language\n{tag}"
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
    def header(cls, tag: Tag) -> str:
        """Make markdown header string."""

        if tag.a is not None:
            title = tag.a.string
            attrs = tag.a.attrs
            anchor = " " + " ".join([f'{key}="{value}"' for key, value in attrs.items()])
            a = f"<a{anchor}></a> "
        else:
            title = tag.string
            a = ""

        if (m := re.match(r"h(?P<level>\d+)", tag.name)) is not None:
            header_level = int(m.group("level"))
        else:
            raise ParsingException(f"Cannot get header level from '{tag.name}'")

        return cls.make_md_head(f"{a}{title}", header_level)

    @staticmethod
    def comment(tag: Tag) -> str:
        """Make comment string."""

        return f"<!--{tag.string}-->"

    @staticmethod
    def paragraph(tag: Tag) -> str:
        """Make paragraph string."""
        s = tag.string

        # TODO parse:
        # <a href="url">name</a> into [name](url)
        # <tt>s</tt> into `s`

        return s
