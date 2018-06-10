import re

escape_regex = re.compile(r'(\*|_|`|~|\\)')
unescape_regex = re.compile(r'\\(\*|_|`|~|\\)')


def escape(text):
    return escape_regex.sub(r'\\\1', text)


def unescape(text):
    return unescape_regex.sub(r'\1', text)
