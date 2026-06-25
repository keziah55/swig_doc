from typing import Optional, Self

from swig_doc.md_utils import code_block, make_md_head, header
from swig_doc.exceptions import ParsingException

import pytest


class MockTag:

    def __init__(
        self,
        tag_name: str,
        attrs: Optional[dict] = None,
        text: str = "",
        children: Optional[dict[:str, Self]] = None,
    ):

        self.string = text

        self._tag = tag_name
        self._attrs = attrs if attrs is not None else {}

        self._children = children if children is not None else {}

    def __getitem__(self, key) -> str:
        return self._attrs.get(key)

    def __getattr__(self, name) -> Self:
        return self._children.get(name)

    def __repr__(self) -> str:
        # attrs = [f'{key}="{value}"' for key, value in self._attrs.items()]
        attrs = []
        for key, value_lst in self._attrs.items():
            attrs += [f'{key}="{value}"' for value in value_lst]

        if len(attrs) > 0:
            attrs_str = " " + " ".join(attrs)
        else:
            attrs_str = ""

        children = [str(child) for child in self._children.values()]
        if len(children):
            children_str = "\n" + "\n".join(children)
        else:
            children_str = ""

        return f"<{self._tag}{attrs_str}>{self.string}{children_str}</{self._tag}>"


@pytest.mark.parametrize(
    "tag, expected",
    [
        (
            MockTag(
                "div",
                attrs={"class": ["targetlang"]},
                children={
                    "pre": MockTag(
                        "pre",
                        text="$ python\n&gt;&gt;&gt; import example\n&gt;&gt;&gt; example.fact(4)\n24\n&gt;&gt;&gt;",
                    )
                },
            ),
            "```python\n$ python\n>>> import example\n>>> example.fact(4)\n24\n>>>\n```",
        ),
        (
            MockTag(
                "div",
                attrs={"class": ["code"]},
                children={
                    "pre": MockTag(
                        "pre",
                        text='/* File: example.i */\n%module example\n\n%{\n#include "example.h"\n%}\n\nint fact(int n);',
                    )
                },
            ),
            '```swig\n/* File: example.i */\n%module example\n\n%{\n#include "example.h"\n%}\n\nint fact(int n);\n```',
        ),
        (
            MockTag(
                "div",
                attrs={"class": ["shell"]},
                children={
                    "pre": MockTag(
                        "pre",
                        text="$ swig -python example.i",
                    )
                },
            ),
            "```shell\n$ swig -python example.i\n```",
        ),
        (
            MockTag(
                "div",
                attrs={"class": ["diagram"]},
                children={
                    "pre": MockTag(
                        "pre",
                        text="mod1.py\npkg1/__init__.py\npkg1/mod2.py\npkg1/pkg2/__init__.py\npkg1/pkg2/mod3.py",
                    )
                },
            ),
            "```\nmod1.py\npkg1/__init__.py\npkg1/mod2.py\npkg1/pkg2/__init__.py\npkg1/pkg2/mod3.py\n```",
        ),
    ],
)
def test_code_block(tag, expected):

    assert code_block(tag, target_language="python") == expected


@pytest.mark.parametrize(
    "tag,err_msg",
    [
        (MockTag("div"), r"Could not get content of 'pre' tag in:\n<div></div>"),
        (
            MockTag(
                "div", attrs={"class": ["a", "b"]}, children={"pre": MockTag("pre", text="demo")}
            ),
            r"Multiple classes in tag; cannot determine code language",
        ),
        (
            MockTag("div", attrs={"class": []}, children={"pre": MockTag("pre", text="demo")}),
            r"No code language class in",
        ),
    ],
)
def test_code_block_error(tag, err_msg):

    with pytest.raises(ParsingException, match=err_msg):
        code_block(tag, target_language="python")


def test_make_md_head():
    assert make_md_head("Heading", level=4) == "#### Heading"
