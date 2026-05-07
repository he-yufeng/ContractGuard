"""Tests for document parsing."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from contractguard.parser import extract_text

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_extract_txt():
    """Test extracting text from a .txt file."""
    text = extract_text(EXAMPLES_DIR / "sample_lease.txt")
    assert "RESIDENTIAL LEASE AGREEMENT" in text
    assert "SECURITY DEPOSIT" in text
    assert len(text) > 100


def test_extract_nonexistent_file():
    """Test error handling for nonexistent file."""
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/path/file.txt")


def test_extract_unsupported_format(tmp_path):
    """Test error handling for unsupported file format."""
    fake_file = tmp_path / "test.xyz"
    fake_file.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text(fake_file)


def test_extract_pdf_without_text_does_not_suggest_missing_ocr_flag(tmp_path, monkeypatch):
    fake_file = tmp_path / "scan.pdf"
    fake_file.write_bytes(b"%PDF-1.4\n")

    class EmptyPage:
        def extract_text(self):
            return None

    class EmptyPdf:
        pages = [EmptyPage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_pdfplumber = SimpleNamespace(open=lambda _path: EmptyPdf())
    monkeypatch.setitem(sys.modules, "pdfplumber", fake_pdfplumber)

    with pytest.raises(ValueError) as exc_info:
        extract_text(fake_file)

    message = str(exc_info.value)
    assert "OCR support is not available yet" in message
    assert "--ocr" not in message


def test_extract_nda():
    """Test extracting text from NDA sample."""
    text = extract_text(EXAMPLES_DIR / "sample_nda.txt")
    assert "NON-DISCLOSURE AGREEMENT" in text
    assert "Confidential Information" in text
