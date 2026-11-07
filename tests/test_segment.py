from hap.segment import estimate_tokens, segment


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
