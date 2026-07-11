from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TagStackItem:
    """Immutable dataclass with open tag and attrs info for a `TagStack` item."""

    name: str
    attrs: dict

    def __repr__(self) -> str:
        return f"'{self.name}' tag with attrs: {self.attrs}"


class TagStack:
    """
    Last-in, first-out stack.

    The methods here do not raise errors if the stack is empty; they simply return `None`.
    """

    def __init__(self):
        self._stack: list[TagStackItem] = []

    def append(self, tag: str, attrs: dict):
        """Add item to stack."""

        self._stack.append(TagStackItem(tag, attrs))

    def pop(self) -> Optional[TagStackItem]:
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
    def current(self) -> Optional[TagStackItem]:
        """
        Return currently open tag.

        Return `None` if there are no open tags.
        """

        if len(self._stack) == 0:
            return None
        return self._stack[-1]

    @property
    def parent(self) -> Optional[TagStackItem]:
        """
        Return parent of currently open tag.

        Return `None` if there is no parent.
        """

        if len(self._stack) < 2:
            return None
        return self._stack[-2]

    @property
    def parents(self) -> Optional[list[TagStackItem]]:
        """
        Return all parent of currently open tag.

        Return `None` if there are no parents.
        """

        if len(self._stack) < 2:
            return None
        else:
            return self._stack[:-2]