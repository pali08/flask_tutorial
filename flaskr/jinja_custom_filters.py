import re


def replace_whitespace(value):
    return re.sub(r'\s+', ' ', value)
