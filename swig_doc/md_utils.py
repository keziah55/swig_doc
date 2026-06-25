from string import Template
import html
import re

from bs4 import Tag

from .exceptions import ParsingException

MARKDOWN_EXT = ".md"

_templates = {"code": Template("```${language}\n${content}\n```")}


def make_md_head(title: str, level: int) -> str:
    """Make markdown header string."""
    return f"{'#' * level} {title}"


def code_block(code_tag: Tag, target_language: str) -> str:
    """
    Make md code block from `<code>` tag.

    The target language must be provided, in case it is needed.
    """

    template = _templates["code"]

    try:
        content = code_tag.pre.string
    except AttributeError as exc:
        raise ParsingException(f"Could not get content of 'pre' tag in:\n{code_tag}") from exc

    # convert html entities into unicode
    content = html.unescape(content)

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


def header(header_tag: Tag) -> str:
    
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

    return make_md_head(f"{a}{title}", header_level)
