import re

escape_regex = re.compile(r'(\*|_|`|~|\\)')
def escape(text):
	return escape_regex.sub(r'\\\1', text)

unescape_regex = re.compile(r'\\(\*|_|`|~|\\)')
def unescape(text):
	return unescape_regex.sub(r'\1', text)
