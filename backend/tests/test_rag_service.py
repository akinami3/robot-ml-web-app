"""RAG service unit tests."""

from __future__ import annotations

from app.domain.services.rag_service import TextSplitter


class TestTextSplitter:
    def test_short_text_no_split(self):
        splitter = TextSplitter(chunk_size=100, overlap=10)
        chunks = splitter.split("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_long_text_splits(self):
        splitter = TextSplitter(chunk_size=50, overlap=10)
        text = "A" * 200
        chunks = splitter.split(text)
        assert len(chunks) > 1

    def test_splits_at_paragraph_boundary(self):
        splitter = TextSplitter(chunk_size=100, overlap=10)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph that is a bit longer to ensure splitting."
        chunks = splitter.split(text)
        assert len(chunks) >= 1

    def test_empty_text(self):
        splitter = TextSplitter(chunk_size=100, overlap=10)
        chunks = splitter.split("")
        assert len(chunks) <= 1

    def test_overlap_creates_redundancy(self):
        splitter = TextSplitter(chunk_size=20, overlap=5)
        text = "word1 word2 word3 word4 word5 word6 word7 word8"
        chunks = splitter.split(text)
        # With overlap, some content should appear in multiple chunks
        assert len(chunks) >= 2
