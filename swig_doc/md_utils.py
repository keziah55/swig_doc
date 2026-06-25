from string import Template
import html

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
    pass
