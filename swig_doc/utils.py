import re

MARKDOWN_EXT = ".md"

HEADER_REGEX = re.compile(r"h(?P<level>\d+)")
