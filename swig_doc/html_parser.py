from html.parser import HTMLParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Self
import warnings
import re

from .md_utils import HtmlToMd, HEADER_REGEX
from .tag_stack import TagStack

# PLAN
# Make DocumentItems for every start tag
# If there is an existing DocItem, it is set as the new DocItem's parent
# When tag ends, do DocItem.to_str()
#   If DocItem has a parent, this string is appended to its data
#   If no parent, string is appended to parser's list
# DocItems are either blocks (p, div, h, ul, ol) or inline (everything else)


@dataclass
class DocumentItem:
    """Class representing document item, either a block item or inline item."""

    tag: str
    doc_pos: tuple[int, int]
    data: list[str] = field(default_factory=list)
    attrs: Optional[dict] = None
    parent: Optional[Self] = None

    _block_tags = ["p", "div", "ul", "ol", "blockquote"]  # also headers

    def __repr__(self) -> str:

        s = f"'{self.tag}' at pos {self.doc_pos}"
        if self.attrs is not None:
            s += ": "
            s += " ".join([f'{k}="{v}"' for k, v in self.attrs.items()])

        # if self.data:
        #     data = "".join(self.data)
        #     data = f"{repr(data)}"
        # else:
        #     data = ""
        # s += f"{data}"

        return s

    @property
    def is_block(self) -> bool:
        """
        Return True if this DocumentItem represents a block of text.

        False if it represents an inline item.
        """
        return self.tag in self._block_tags or (HEADER_REGEX.match(self.tag) is not None)

    def to_str(self) -> str:
        """Return markdown string of this `DocumentItem`."""

        if self.tag == "a":
            return self._link_to_str()

        if self.data is None:
            return ""

        # join_str = "\n" if self.tag in ["ol", "ul"] else ""

        # if self.tag in ["ol", "ul"]:
        #     print(self.data)

        s = "".join(self.data)

        # if re.match(r"h\d+", self.tag):
        #     s = re.sub(r"\n", "", s)
        # s = f"\n{s}\n"

        if self.is_block:
            ret = f"\n{s}\n"
        elif self.tag == "li":
            ret = f"{s}\n"
        else:
            ret = s

        return ret

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

        if data is None or data == "":
            return

        self.data.append(data)


class HtmlPageParser(HTMLParser):

    def __init__(self, target_language: Optional[str] = None):
        super().__init__()

        self.reset(target_language)
        self._data_tags = ["p", "blockquote"]

    def reset(self, target_language: Optional[str] = None):
        super().reset()

        if target_language is None:
            target_language = ""

        HtmlToMd.set_target_language(target_language)

        # list of strings from completed DocumentItems
        self._doc_parts: list[str] = []

        # list of open DocumentItems
        self._doc_items = TagStack()

        self._active = True

    @property
    def doc(self) -> str:
        """Return markdown document."""

        # parts = [doc_item.to_str() for doc_item in self._doc_items]
        s = "".join(self._doc_parts)

        # s = re.sub(r"\n\n\n+", "\n\n", s)

        return s

    def parse(self, html_file: Path) -> str:
        """Convert html file content to markdown."""

        self.feed(html_file.read_text())
        return self.doc

    def _handle_tag(self, tag: str, mode: str, attrs: Optional[dict] = None) -> bool:
        """Return True if parser should handle this tag."""

        if mode == "start":
            if (tag == "div" and "sectiontoc" in attrs.get("class", "")) or tag in ["title"]:
                self._active = False
                return False

        elif mode == "end":
            if not self._active and tag in ["div", "title"]:
                self._active = True
                return False

        if not self._active or tag in ["link", "meta"]:
            return False

        return True

    def _new_doc_item(self, tag, **kwargs) -> DocumentItem:

        # if len(self._doc_items) > 0:
        parent = self._doc_items.current  # None if stack is empty
        # else:
        #     parent = None

        item = DocumentItem(tag=tag, doc_pos=self.getpos(), parent=parent, **kwargs)
        self._doc_items.append(item)

        return item

    def _close_doc_item(self, item: DocumentItem):

        item_str = item.to_str()

        if item.parent is not None:
            item.parent.append_data(item_str)
        else:
            self._doc_parts.append(item_str)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]):
        """Handle a tag opening."""

        attrs = dict(attrs)

        if not self._handle_tag(tag, attrs=attrs, mode="start"):
            return

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := HtmlToMd.get(tag)) is not None:
            s = func("start", parent=item.parent)
            item.append_data(s)

    def handle_endtag(self, tag: str):
        """Handle a tag closing."""

        # print(f"END    {tag}")

        if not self._handle_tag(tag, mode="end"):
            return

        item = self._doc_items.pop()
        while item is not None and item.tag != tag:
            if item is None:
                warnings.warn(
                    f"End tag '{tag}' encountered at {self.getpos()}, but no tags are open"
                )
                break

            warnings.warn(
                f"End tag '{tag}' encountered at {self.getpos()}, but unclosed {item} remains"
            )

            # close previous doc item
            self._close_doc_item(item)

            # pop next doc item
            item = self._doc_items.pop()

        if item is None:
            return

        if (func := HtmlToMd.get(tag)) is not None:
            s = func("end", parent=item.parent)
            item.append_data(s)

        self._close_doc_item(item)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str]]):
        """Handle a self-closing tag."""

        if not self._active:
            return

        attrs = dict(attrs)

        # print(f"ST/END {tag} {attrs}")

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := HtmlToMd.get(tag)) is not None:
            s = func(parent=item.parent)
            item.append_data(s)

        self._doc_items.pop()
        self._close_doc_item(item)

    def handle_data(self, data: str):
        """Handle data within or outwith a tag."""

        if not self._active:
            return

        # data = data.strip()
        if not data.strip():
            return

        if len(self._doc_items) > 0:
            item = self._doc_items.current
        else:
            item = self._new_doc_item(tag="string")
            print(f"New item for '{data}'")

        if item.tag in self._data_tags:
            func = HtmlToMd.get(item.tag)
            data = func("data", data=data)

        item.append_data(data)

    def handle_comment(self, data: str):
        """Handle comment tag."""

        if not self._active:
            return

        data = f"<!--{data}-->\n"

        item = self._new_doc_item("comment", data=[data])
        self._doc_items.pop()
        self._close_doc_item(item)


if __name__ == "__main__":

    html_file = Path(__file__).parents[1].joinpath("tests", "data", "convert_text_format.html")

    parser = HtmlPageParser(target_language="python")
    md = parser.parse(html_file)
    print(md)
    # parser.feed(html_file.read_text())
    # print(parser.doc)
