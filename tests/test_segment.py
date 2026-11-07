from hap.segment import _units, estimate_tokens, segment


def test_empty_input_has_no_chunks():
    assert segment("") == []


def test_short_input_is_one_chunk():
    chunks = segment("Hi.")
    assert len(chunks) == 1
    assert chunks[0].text == "Hi."


def test_chunks_are_exact_slices():
    text = ("Alpha beta gamma. " * 40 + "\n\n") * 30
    for c in segment(text, max_tokens=50, overlap_tokens=10):
        assert text[c.start : c.end] == c.text


def test_every_character_is_covered():
    text = "Sentence number one. Another one follows! Is this a question? " * 60
    covered = [False] * len(text)
    for c in segment(text, max_tokens=40, overlap_tokens=10):
        for i in range(c.start, c.end):
            covered[i] = True
    assert all(covered)


def test_chunks_respect_size_cap():
    text = "word " * 5000  # no sentence boundaries at all
    for c in segment(text, max_tokens=50, overlap_tokens=10):
        assert estimate_tokens(c.text) <= 50


def test_unbroken_text_is_hard_split():
    text = "x" * 1000
    chunks = segment(text, max_tokens=50, overlap_tokens=0)
    assert all(len(c.text) <= 150 for c in chunks)
    assert "".join(c.text for c in chunks) == text


def test_consecutive_chunks_overlap_and_progress():
    text = "One two three. " * 200
    chunks = segment(text, max_tokens=60, overlap_tokens=20)
    assert len(chunks) > 1
    for a, b in zip(chunks, chunks[1:]):
        assert b.start > a.start
        assert b.start <= a.end


def _cuts(text, max_tokens=1000):
    return [a for a, _ in _units(text, max_tokens * 3)][1:]


def test_inline_code_with_ellipsis_is_never_split():
    text = "Use `INSERT ... ON CONFLICT DO NOTHING` here. Next sentence."
    assert _cuts(text) == [text.index("Next")]


def test_fenced_block_with_blank_lines_stays_whole():
    text = "Intro.\n\n```sql\nSELECT 1.\n\nSELECT 2. Done.\n```\n\nAfter."
    start, end = text.index("```sql"), text.index("```\n\nAfter") + 3
    assert not [c for c in _cuts(text) if start < c < end]


def test_ellipsis_in_prose_is_not_a_sentence_end():
    text = "Wait... what happened here? Nothing."
    assert _cuts(text) == [text.index("Nothing")]


def test_oversize_code_block_splits_on_newlines_not_mid_line():
    lines = [f"line number {i} of the code" for i in range(40)]
    text = "```\n" + "\n".join(lines) + "\n```"
    for a, b in _units(text, 300):
        assert text[a:b].endswith("\n") or b == len(text)
