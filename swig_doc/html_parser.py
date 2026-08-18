from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
import warnings
import re


from .doc_item import DocumentItem, DocItemStack, TableItem
from .md_utils import HtmlToMd, transform_internal_link
from .utils import make_html_tag
from .exceptions import EndTagWarning


class HtmlPageParser(HTMLParser):

    def __init__(
        self,
        target_language: Optional[str] = None,
        shell_language: Optional[str] = None,
        quiet: bool = True,
        embed_html_tags: Optional[list[str]] = None,
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

        # these tags should be self-closing; if we get a start tag for them, close it
        # immediately
        self._self_closing = ["br", "hr", "img"]

        self._data_tags = ["p", "blockquote"]

        # tags that should be copied directly into markdown output
        self._embed_html_tags = embed_html_tags if embed_html_tags is not None else []

        self._quiet = quiet

        self.reset(target_language, shell_language)

    def reset(
        self, target_language: Optional[str] = None, shell_language: Optional[str] = None
    ):
        """
        Reset all internal objects.

        Also call `super().reset()`.
        """

        super().reset()

        self._html_to_md = HtmlToMd(target_language=target_language, shell_language=shell_language)

        self._page_title: Optional[str] = None

        # list of strings from completed DocumentItems
        self._doc_parts: list[str] = []

        # list of open DocumentItems
        self._doc_items = DocItemStack()

        self._active = True

        self._table_item: Optional[TableItem] = None
        self._force_handle_table = False

        self._last_start_tag: Optional[str] = None

    def close(self):
        """
        Close any remaining items.

        Also call `super().close()`.
        """

        if len(self._doc_items) > 0:
            self._close_doc_items(None)

        super().close()

    @property
    def doc(self) -> str:
        """Return markdown document."""

        s = "".join(self._doc_parts)
        s = re.sub(r"\n\n\n+", "\n\n", s)

        return s

    @property
    def title(self) -> Optional[str]:
        """Return page title, if set."""
        return self._page_title

    def parse(self, html_file: Path, auto_close: bool = True) -> str:
        """
        Convert html file content to markdown.

        If `auto_close`, call `close()` before returning. This may be necessary to handle
        any unclosed html tags in the document.

        """

        self.feed(html_file.read_text())

        if auto_close:
            self.close()

        return self.doc

    def _append_str(self, s: str):
        """Append string to open `DocumentItem` or `_doc_parts` list."""

        if len(self._doc_items) > 0:
            # append string to current item data
            item = self._doc_items.current
            item.append_data(s)
        else:
            # if no open doc item, append directly to `_doc_parts` list
            self._doc_parts.append(s)

    def _handle_tag(self, tag: str, mode: str, attrs: Optional[dict] = None) -> bool:
        """Return True if parser should handle this tag."""

        if tag in self._embed_html_tags:
            self._embed_html(tag=tag, mode=mode, attrs=attrs)
            return False

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

    def _embed_html(self, tag: str, mode: str, attrs: Optional[dict] = None):
        """Make html tag and append to document."""

        html = make_html_tag(mode=mode, tag=tag, attrs=attrs)
        self._append_str(html)

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

    def _close_doc_items(self, stop_tag: Optional[str]) -> Optional[DocumentItem]:
        """
        Close any open doc items until a tag matching `stop_tag` is found.

        If `stop_tag` is None, close all open doc items.

        Return the last item or None.
        """

        item = self._doc_items.pop()

        while item is not None:

            if stop_tag is not None and item.tag == stop_tag:
                break

            if stop_tag is not None:
                prefix = f"End tag '{stop_tag}' encountered at {self.getpos()}; "
            else:
                prefix = ""

            if item is None:
                warnings.warn(f"{prefix}no tags are open", EndTagWarning)
                break

            warnings.warn(f"{prefix}force close {item}", EndTagWarning)

            # close doc item
            self._close_doc_item(item)

            # pop next doc item
            item = self._doc_items.pop()

        return item

    def _close_table(self):

        if self._table_item is None:
            return

        if self._table_item.can_be_converted:
            self._force_handle_table = True
            for func_name, tag, kwargs in self._table_item.function_calls:
                func = getattr(self, func_name)
                func(tag, **kwargs)

        else:
            table_html = self._table_item.table_html
            self._append_str(table_html)

        self._table_item = None
        self._force_handle_table = False

    @property
    def _send_table_data_to_item(self) -> bool:
        """Return True if `_table_item` should be used to handle tags/data."""

        return self._force_handle_table is False and self._table_item is not None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]):
        """Handle a tag opening."""

        attrs = dict(attrs)

        self._last_start_tag = tag

        if not self._quiet:
            if self._doc_items.current is not None:
                ci = f"; current: {self._doc_items.current.tag}"
            else:
                ci = ""
            print(f"START: {tag}{ci}")

        if tag == "a" and "href" in attrs:
            attrs["href"] = transform_internal_link(attrs["href"])

        if not self._handle_tag(tag, attrs=attrs, mode="start"):
            return

        if not self._force_handle_table and tag == "table" and self._table_item is None:
            self._table_item = TableItem()

        if self._send_table_data_to_item:
            self._table_item.append_data(tag, attrs, mode="start")
            return

        possible_unclosed = {"li": ["li"], "dd": ["dt", "dd"], "dt": ["dd"], "p": ["p"]}
        if self._doc_items.current is not None:
            for unclosed_tag, unclosed_tag_parents in possible_unclosed.items():
                if tag == unclosed_tag and self._doc_items.current.tag in unclosed_tag_parents:
                    # <li>, <dt> or <dd> might not be closed, so end tag manually here
                    if not self._quiet:
                        print(f"Force end tag {self._doc_items.current.tag}")
                    self.handle_endtag(self._doc_items.current.tag)

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := self._html_to_md.get(tag)) is not None:
            s = func("start", parent=item.parent)
            item.append_data(s)

        if tag in self._self_closing:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str):
        """Handle a tag closing."""

        if not self._quiet:
            print(f"END:   {tag}")

        if not self._handle_tag(tag, mode="end"):
            return

        if self._send_table_data_to_item:
            self._table_item.append_data(tag, mode="end")
            if self._table_item.is_complete:
                self._close_table()
            return

        item = self._close_doc_items(tag)
        if item is None:
            return

        if (func := self._html_to_md.get(tag)) is not None:
            s = func(mode="end", parent=item.parent)
            item.append_data(s)

        self._close_doc_item(item)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str]]):
        """Handle a self-closing tag."""

        if not self._active:
            return

        attrs = dict(attrs)

        if tag in self._embed_html_tags:
            self._embed_html(tag=tag, mode="startend", attrs=attrs)
            return

        if self._send_table_data_to_item:
            self._table_item.append_data(tag, attrs, mode="startend")
            return

        item = self._new_doc_item(tag, attrs=attrs)

        if (func := self._html_to_md.get(tag)) is not None:
            s = func(parent=item.parent)
            item.append_data(s)

        self._doc_items.pop()
        self._close_doc_item(item)

    def handle_data(self, data: str):
        """Handle data within or outwith a tag."""

        if self._last_start_tag == "title" and self._page_title is None and data.strip():
            self._page_title = data.strip()
            return

        ci = self._doc_items.current.tag if self._doc_items.current is not None else None

        if not self._quiet:
            print(f"DATA:  {repr(data)}; current item: {ci}")

        if not self._active:
            return

        if not data.strip() and ci != "p":
            return

        if self._send_table_data_to_item:
            self._table_item.append_data(data, mode="data")
            return

        if len(self._doc_items) > 0:
            item = self._doc_items.current
        else:
            item = self._new_doc_item(tag="string")

        if item.tag in self._data_tags:
            func = self._html_to_md.get(item.tag)
            data = func("data", data=data)

        item.append_data(data)

    def handle_comment(self, data: str):
        """Handle comment tag."""

        if not self._active:
            return

        html = make_html_tag(mode="comment", tag=data) + "\n"

        if self._send_table_data_to_item:
            self._table_item.append_data(html, mode="data")
            return

        self._append_str(html)

    def handle_entityref(self, name):
        """Handle `&[name];` entities (as we are using `convert_charrefs=False`)."""

        if not self._active:
            return

        if self._send_table_data_to_item:
            self._table_item.append_data(name, mode="entityref")
            return

        char = self._entity_refs.get(name, None)

        if char is not None:
            if len(self._doc_items) > 0:
                item = self._doc_items.current
            else:
                item = self._new_doc_item(tag="string")

            if char == ">":
                if item.tag not in ["pre", "tt"]:
                    char = f"\\{char}"

            item.append_data(char)
