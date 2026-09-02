"""Split text into sentences.

Argos ships a stanza tokeniser inside every model, and stanza drags in torch,
which is about 2.5 GB. That is most of an installer for the sake of deciding
where a full stop ends a sentence, so LingoGeek does its own splitting and
never unpacks the stanza folder at all.

The rules below are deliberately conservative. Over-splitting produces worse
translation than under-splitting, because the model loses the context it needs
to get agreement and word order right, so anything ambiguous stays joined.
"""
from __future__ import annotations

import re

# Abbreviations that end in a full stop without ending the sentence.
_ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "rev", "hon",
    "no", "vs", "etc", "eg", "ie", "cf", "al", "inc", "ltd", "plc", "co",
    "approx", "dept", "est", "fig", "min", "max", "vol", "pp", "ed",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun",
}

_BOUNDARY = re.compile(r"([.!?…。！？])([\"'”’\)\]]*)(\s+)")


def _looks_like_abbreviation(text: str, dot_index: int) -> bool:
    """True when the full stop at dot_index is part of an abbreviation."""
    start = dot_index
    while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "."):
        start -= 1
    word = text[start:dot_index].strip(".").lower()
    if not word:
        return False
    if word in _ABBREV:
        return True
    # Single initials: "J. Smith", and dotted forms like "U.S.A"
    if len(word) == 1 and word.isalpha():
        return True
    if "." in text[start:dot_index]:
        return True
    return False


def split(text: str) -> list[str]:
    """Split one paragraph of text into sentences, keeping the punctuation."""
    text = text.strip()
    if not text:
        return []

    out: list[str] = []
    last = 0
    for m in _BOUNDARY.finditer(text):
        dot = m.start(1)
        if m.group(1) == "." and _looks_like_abbreviation(text, dot):
            continue
        end = m.end(2)
        # A sentence of one or two characters is almost always a false positive.
        if end - last < 3:
            continue
        # Do not split when the next character cannot start a sentence.
        rest = text[m.end():]
        if rest and rest[0].islower():
            continue
        out.append(text[last:end].strip())
        last = m.end()

    tail = text[last:].strip()
    if tail:
        out.append(tail)
    return out or [text]
