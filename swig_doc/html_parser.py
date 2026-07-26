from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
import warnings
import re


from .doc_item import DocumentItem, DocItemStack
from .md_utils import HtmlToMd, transform_internal_link
from .exceptions import EndTagWarning


class HtmlPageParser(HTMLParser):

    def __init__(
        self,
        target_language: Optional[str] = None,
        shell_language: Optional[str] = None,
        quiet: bool = True,
    ):
        super().__init__(convert_charrefs=False)

        self._entity_refs = {
            "lt": "<",
            "gt": ">",
            "amp": "&",
            "nbsp": " ",
            "quot": '"',
            "ndash": "-",
            "hellip": "...",
            "uarr": chr(8593),
            "darr": chr(8595),
        }

        self._quiet = quiet
        self.reset(target_language, shell_language)
        self._data_tags = ["p", "blockquote"]

    def reset(
        self, target_language: Optional[str] = None, shell_language: Optional[str] = None
    ):
        super().reset()

        HtmlToMd.set_target_language(target_language)
        HtmlToMd.set_shell_language(shell_language)

        # list of strings from completed DocumentItems
        self._doc_parts: list[str] = []

        # list of open DocumentItems
        self._doc_items = DocItemStack()

        self._active = True

    @property
    def doc(self) -> str:
        """Return markdown document."""

        s = "".join(self._doc_parts)

        s = re.sub(r"\n\n\n+", "\n\n", s)

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

        parent = self._doc_items.current  # None if stack is empty

        item = DocumentItem(
            tag=tag, doc_pos=self.getpos(), parent=parent, _quiet=self._quiet, **kwargs
        )
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

        if not self._quiet:
            print(f"START: {tag} {attrs}")

        if tag == "a" and "href" in attrs:
            attrs["href"] = transform_internal_link(attrs["href"])

        if not self._handle_tag(tag, attrs=attrs, mode="start"):
            return

        if tag == "li" and self._doc_items.current.tag == "li":
            # <li> might not be closed, so end tag manually here
            self.handle_endtag("li")

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := HtmlToMd.get(tag)) is not None:
            s = func("start", parent=item.parent)
            item.append_data(s)

    def handle_endtag(self, tag: str):
        """Handle a tag closing."""

        if not self._quiet:
            print(f"END:  {tag}")

        if not self._handle_tag(tag, mode="end"):
            return

        item = self._doc_items.pop()
        while item is not None and item.tag != tag:
            if item is None:
                warnings.warn(
                    f"End tag '{tag}' encountered at {self.getpos()}, but no tags are open",
                    EndTagWarning,
                )
                break

            warnings.warn(
                f"End tag '{tag}' encountered at {self.getpos()}, but unclosed {item} remains",
                EndTagWarning,
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

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := HtmlToMd.get(tag)) is not None:
            s = func(parent=item.parent)
            item.append_data(s)

        self._doc_items.pop()
        self._close_doc_item(item)

    def handle_data(self, data: str):
        """Handle data within or outwith a tag."""

        ci = self._doc_items.current.tag if self._doc_items.current is not None else None

        if not self._quiet:
            print(f"DATA:  {repr(data)}; current item: {ci}")

        if not self._active:
            return

        if not data.strip() and ci != "p":
            return

        if len(self._doc_items) > 0:
            item = self._doc_items.current
        else:
            item = self._new_doc_item(tag="string")

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

    def handle_entityref(self, name):
        """Handle `&[name];` entities (as we are using `convert_charrefs=False`)."""

        char = self._entity_refs.get(name, None)

        if char is not None:
            if len(self._doc_items) > 0:
                item = self._doc_items.current
            else:
                item = self._new_doc_item(tag="string")

            if char == ">":
                char = f"\\{char}"

                # # check if we're in the "Java/Python Doxygen tags" table
                # if (table := item.search_parents("table")) is not None:
                #     if table.attrs.get("summary", "") in [
                #         "Java Doxygen tags",
                #         "Python Doxygen tags",
                #         "CSharp XML Doxygen tags"
                #     ]:
                #         char = f"\\{char}"

            item.append_data(char)
