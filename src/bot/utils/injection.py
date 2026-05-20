import re

_PATTERNS = [
    re.compile(r"(?i)ignore\s+(your|the)?\s*(previous|above|all)?\s*instructions"),
    re.compile(r"(?i)you\s+are\s+now\s+[a-z ]{3,40}"),
    re.compile(r"(?i)disregard\s+(your|the)\s+(system|prior|previous)"),
    re.compile(r"<\|im_start\|>|<\|im_end\|>"),
    re.compile(r"(?i)system\s*:\s*you\s+are"),
    re.compile(r"(?i)</?(system|assistant)>"),
    re.compile(r"(?i)forget\s+(everything|all|your)\s+(above|prior|previous)"),
    re.compile(r"(?i)new\s+instructions?\s*:"),
]


def is_tainted(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in _PATTERNS)


__all__ = ["is_tainted"]
