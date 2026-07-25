from dataclasses import dataclass, field
from typing import Optional, Self
import re
from .utils import HEADER_REGEX


@dataclass
class DocumentItem:
    """Class representing document item, either a block item or inline item."""

    tag: str
    doc_pos: tuple[int, int]
    data: list[str] = field(default_factory=list)
    attrs: Optional[dict] = None
    parent: Optional[Self] = None

    _quiet: bool = True

    _block_tags = ["p", "div", "ul", "ol", "blockquote"]  # also headers

    def __repr__(self) -> str:

        s = f"'{self.tag}' at pos {self.doc_pos}"
        if self.attrs:
            s += ": "
            s += " ".join([f'{k}="{v}"' for k, v in self.attrs.items()])

        return s

    @property
    def is_block(self) -> bool:
        """
        Return True if this DocumentItem represents a block of text.

        False if it represents an inline item.
        """
        return self.tag in self._block_tags or self.is_header

    @property
    def is_header(self) -> bool:
        """Return True if this DocumentItem represents a header tag."""
        return HEADER_REGEX.match(self.tag) is not None

    def to_str(self) -> str:
        """Return markdown string of this `DocumentItem`."""

        if self.tag == "a":
            return self._link_to_str()

        if self.data is None:
            return ""

        if not self._quiet and self.tag in ["ol", "ul"]:
            print(f"{self.tag}: {self.data}")

        s = "".join(self.data)

        if self.tag in ["li"]:
            # s = s.lstrip()
            s = s.rstrip()
        elif self.tag in ["p"]:
            s = s.strip()
        elif self.tag == "table":
            if (
                caption := self.attrs.get("caption", self.attrs.get("summary", None))
            ) is not None:
                s += f"\n**Table:** {caption}\n"
        elif self.tag == "tr":

            if (table := self.search_parents("table")) is not None:
                if len(table.data) == 0:
                    # this is end of first table row, need to add header underline
                    # count number of '|' in this row (not including any escaped '|')
                    num_cols = len(re.findall(r"(?<!\\)\|", s)) - 1
                    underline = "|".join(["---"] * num_cols)
                    s += f"|{underline}|\n"

        if self.is_block:
            ret = f"\n{s}\n"
        elif self.tag == "li":
            ret = f"{s}\n"
        else:
            ret = s

        return ret

    def search_parents(self, tag: str) -> Optional[Self]:
        """Search for `tag` in parents."""

        parent = self.parent

        while parent is not None:
            if parent.tag == tag:
                break
            else:
                parent = parent.parent

        return parent

    def _link_to_str(self) -> str:
        """Return markdown string representation of link/anchor."""

        anchor = self.attrs.get("name", None)
        url = self.attrs.get("href", None)

        title = "".join(self.data)

        if title is not None and anchor is not None:
            s = f'<a name="{anchor}"></a> {title}'
        elif title is not None and url is not None:
            s = f"[{title}]({url})"
        else:
            raise Exception(
                f"LinkItem requires title and either anchor or url\n"
                f"{title=}, {url=}, {anchor=}"
            )

        s = re.sub(r"\n", " ", s)
        return s

    def append_data(self, data: Optional[str]):
        """Add more `data` to this item."""

        if len(self.data) == 1 and self.tag in ["li"]:
            data = data.lstrip()

        if data is None or data == "":
            return

        self.data.append(data)


class DocItemStack:
    """
    Last-in, first-out stack.

    The methods here do not raise errors if the stack is empty; they simply return `None`.
    """

    def __init__(self):
        self._stack: list[DocumentItem] = []

    def __len__(self):
        return len(self._stack)

    def append(self, item):
        """Add item to stack."""
        self._stack.append(item)

    def pop(self) -> Optional[DocumentItem]:
        """
        Remove and return last item from stack.

        Return `None` if stack is empty.
        """

        try:
            item = self._stack.pop()
        except IndexError:
            return None
        else:
            return item

    @property
    def current(self) -> Optional[DocumentItem]:
        """
        Return currently open tag.

        Return `None` if there are no open tags.
        """

        if len(self._stack) == 0:
            return None
        return self._stack[-1]

    @property
    def parent(self) -> Optional[DocumentItem]:
        """
        Return parent of currently open tag.

        Return `None` if there is no parent.
        """

        if len(self._stack) < 2:
            return None
        return self._stack[-2]

    @property
    def parents(self) -> Optional[list[DocumentItem]]:
        """
        Return all parent of currently open tag.

        Return `None` if there are no parents.
        """

        if len(self._stack) < 2:
            return None
        else:
            return self._stack[:-2]
