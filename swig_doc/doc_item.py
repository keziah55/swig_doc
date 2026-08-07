from dataclasses import dataclass, field
from typing import Optional, Self, Literal
import re
from .utils import HEADER_REGEX, make_html_tag


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
    _inline_tags = ["tt", "em", "i", "strong", "b", "s", "sub", "sup", "mark", "q"]

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
            # ensure all columns are the same length and add underline
            s = self._format_table(s)

            if (
                caption := self.attrs.get("caption", self.attrs.get("summary", None))
            ) is not None:
                s += f"\n**Table:** {caption}\n"

        elif self.tag == "dl":
            lines = s.split("\n")
            for n, line in enumerate(lines):
                if not line.startswith("-"):
                    line = line.strip()
                    if line:
                        lines[n] = f"    {line}"
            s = "\n".join(lines)

        elif self.tag == "tt":
            # tt tag is wrapped with single backquote; if there are multiple lines,
            # switch to triple backquotes
            if "\n" in s:
                s = f"```\n{s.strip('\n`')}\n```"

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

    @staticmethod
    def _count_pipe(s: str) -> int:
        """Return number of '|' in this `s` (not including any escaped '|')."""

        return len(re.findall(r"(?<!\\)\|", s))

    def _get_table_columns(self, data_str: str) -> tuple[list[str], list[int]]:
        """
        Get number of columns in each row.

        Note that this may include `-1` for empty rows.
        """

        # rows = [f"{row}|" for row in re.split(r"\| *\n", data_str) if row]
        rows = data_str.split("\n")
        return rows, [self._count_pipe(row) - 1 for row in rows]

    def _format_table(self, data_str: str) -> str:
        """Ensure all table columns have the correct width and add header underline."""

        rows, num_cols = self._get_table_columns(data_str)

        max_cols = max(num_cols)

        if len(set([num for num in num_cols if num > 0])) > 1:
            # only need to set fixed width if there are shorter rows
            for n, row in enumerate(rows):
                row_len = self._count_pipe(row) - 1
                if num_cols[n] < 0 or row_len == max_cols:
                    continue

                rows[n] += " |" * (max_cols - row_len)

        header_idx = None
        for n, row in enumerate(rows):
            if len(row.strip()) > 1:
                header_idx = n + 1
                break

        underline = "|".join(["---"] * max_cols)
        rows = rows[:header_idx] + [f"|{underline}|"] + rows[header_idx:]

        return "\n".join(rows) + "\n"

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
        elif self.tag in ["td", "th"]:
            data = re.sub(r"\n+", " ", data)
        elif len(self.data) == 1 and self.tag in self._inline_tags:
            data = data.strip(" ")

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


class TableItem:
    """
    Class to gather html table data.

    Each `handle_[name]` function call from `HtmlParser` is logged by calling
    `append_data`.

    The table can then be reconstructed into html, with the `table_html` property,
    or can be converted into markdown via a list of `HtmlParser` function names and args
    (`function_calls` property).

    """

    def __init__(self):

        self._data = []

        # tags/attrs that, if present within table, mean the table should stay as html
        self._unhandled_tags = ["pre"]
        self._unhandled_attrs = ["colspan"]

        self._can_be_converted = True
        self._active = True

    @property
    def can_be_converted(self) -> bool:
        """True if html table can be converted to markdown."""
        return self._can_be_converted

    @property
    def is_complete(self) -> bool:
        """False if table data has not yet all been gathered."""
        return not self._active

    @property
    def table_html(self) -> str:
        """Return table html as string."""

        s = ""

        for mode, tag, attrs in self._data:
            if mode == "entityref":
                s += f"&{tag};"
            elif mode == "data":
                s += tag
            else:
                s += make_html_tag(mode, tag, attrs, new_line=False)

        return s

    @property
    def function_calls(self) -> list[tuple[str, str, dict]]:
        """
        Return list of function calls and args to process the html into markdown.

        First item in each tuple is the function name, then the `tag` string, then
        `kwargs` dict.
        """

        lst = []

        for mode, tag, attrs in self._data:
            func_name = f"handle_{mode}"
            if mode in ["start", "startend", "end"]:
                func_name += "tag"

            kwargs = {}
            if attrs is not None:
                kwargs["attrs"] = list(attrs.items())

            lst.append((func_name, tag, kwargs))

        return lst

    def append_data(
        self,
        tag: str,
        attrs: Optional[dict] = None,
        mode: Literal["start", "startend", "end", "data", "entityref"] = "data",
    ):
        """Append table tags/data."""

        self._data.append((mode, tag, attrs))

        if tag in self._unhandled_tags:
            self._can_be_converted = False
        elif attrs is not None and any(key in attrs for key in self._unhandled_attrs):
            self._can_be_converted = False

        if mode == "end" and tag == "table":
            self._active = False
