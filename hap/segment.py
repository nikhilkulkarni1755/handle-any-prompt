import re

from hap.schemas import Chunk

CHARS_PER_TOKEN = 3  # conservative: small models lack reliable public tokenizers
BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n\s*\n")


def estimate_tokens(text: str) -> int:
    return -(-len(text) // CHARS_PER_TOKEN)


def _units(text: str, max_chars: int) -> list[tuple[int, int]]:
    cuts = [0] + [m.end() for m in BOUNDARY.finditer(text)] + [len(text)]
    units = []
    for a, b in zip(cuts, cuts[1:]):
        while b - a > max_chars:
            window = text[a : a + max_chars]
            ws = max(window.rfind(" "), window.rfind("\n"))
            cut = a + ws + 1 if ws > 0 else a + max_chars
            units.append((a, cut))
            a = cut
        if b > a:
            units.append((a, b))
    return units


def segment(text: str, max_tokens: int = 300, overlap_tokens: int = 50) -> list[Chunk]:
    """Split text into chunks that are exact slices of it, overlapping at unit boundaries."""
    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN
    units = _units(text, max_chars)
    chunks: list[Chunk] = []
    i = 0
    while i < len(units):
        j = i
        while j < len(units) and units[j][1] - units[i][0] <= max_chars:
            j += 1
        start, end = units[i][0], units[j - 1][1]
        chunks.append(Chunk(index=len(chunks), start=start, end=end, text=text[start:end]))
        if j == len(units):
            break
        k = i + 1
        while k < j and end - units[k][0] > overlap_chars:
            k += 1
        i = k
    return chunks
