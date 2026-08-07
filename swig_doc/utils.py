import re
from string import Template
from typing import Optional, Literal

MARKDOWN_EXT = ".md"

HEADER_REGEX = re.compile(r"h(?P<level>\d+)")

REDIRECT_TEMPLATE = Template(
    """<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url=$url">
        <script type="text/javascript">
            window.location.href = "$url"
        </script>
        <title>Page Redirection</title>
    </head>
    <body>
        <!-- Note: don't tell people to `click` the link, just tell them that it is a link. -->
        If you are not redirected automatically, follow this <a href="$url">link to example</a>.
    </body>
</html>
"""
)


def make_html_tag(
    mode: Literal["start", "startend", "end", "comment"],
    tag: str,
    attrs: Optional[dict] = None,
    new_line: bool = True,
) -> str:
    """Make html tag."""

    match mode:
        case "end":
            s = f"</{tag}>"
        case "comment":
            s = f"<!--{tag}-->"
        case "start" | "startend":
            if attrs:
                attrs_str = " ".join([f'{key}="{value}"' for key, value in attrs.items()])
                attrs_str = " " + attrs_str
            else:
                attrs_str = ""

            open_str = "<"
            close_str = "/>" if mode == "startend" else ">"
            s = f"{open_str}{tag}{attrs_str}{close_str}"

        case _:
            raise ValueError(f"Unknown html tag mode '{mode}'")

    if new_line:
        s += "\n"

    return s
