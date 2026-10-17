import re


def extract_letters(s: str) -> str:
    s = re.sub(r'\W', '', s)
    return s.lower()