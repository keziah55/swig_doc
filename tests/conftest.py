from pathlib import Path
from typing import Optional, Self

import pytest


@pytest.fixture
def data_dir():
    return Path(__file__).parent.joinpath("data")


class MockTag:

    def __init__(
        self,
        tag_name: str,
        attrs: Optional[dict] = None,
        text: str = "",
        children: Optional[list[Self]] = None,
    ):

        self.string = text

        self.name = tag_name
        self.attrs = attrs if attrs is not None else {}

        self._children = (
            {child.name: child for child in children} if children is not None else {}
        )

    def __getitem__(self, key) -> str:
        return self.attrs.get(key)

    def __getattr__(self, name) -> Self:
        return self._children.get(name)

    def __repr__(self) -> str:
        # attrs = [f'{key}="{value}"' for key, value in self._attrs.items()]
        attrs = []
        for key, value_lst in self.attrs.items():
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

        return f"<{self.name}{attrs_str}>{self.string}{children_str}</{self.name}>"
