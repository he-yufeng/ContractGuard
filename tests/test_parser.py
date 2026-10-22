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


def test_extract_pdf_without_text_points_at_ocr_install(tmp_path, monkeypatch):
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
    # no pytesseract on this host: the error must say how to get OCR working
    monkeypatch.setitem(sys.modules, "pytesseract", None)

    with pytest.raises(ValueError) as exc_info:
        extract_text(fake_file)

    message = str(exc_info.value)
    assert "contractguard[ocr]" in message
    assert "tesseract" in message.lower()


def test_pdf_with_real_text_does_not_touch_ocr(tmp_path, monkeypatch):
    fake_file = tmp_path / "text.pdf"
    fake_file.write_bytes(b"%PDF-1.4\n")

    class TextPage:
        def extract_text(self):
            return "RESIDENTIAL LEASE AGREEMENT " * 5

    class TextPdf:
        pages = [TextPage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fail_ocr(_path):
        raise AssertionError("OCR must not run when embedded text is enough")

    monkeypatch.setitem(
        sys.modules, "pdfplumber", SimpleNamespace(open=lambda _path: TextPdf())
    )
    monkeypatch.setattr("contractguard.parser._ocr_pdf", _fail_ocr)

    assert "RESIDENTIAL LEASE AGREEMENT" in extract_text(fake_file)


def test_ocr_path_joins_pages_and_picks_languages(tmp_path, monkeypatch):
    from contractguard import parser

    fake_file = tmp_path / "scan.pdf"
    fake_file.write_bytes(b"%PDF-1.4\n")

    class FakePage:
        def render(self, scale):
            return SimpleNamespace(to_pil=lambda: object())

    class FakePdf:
        def __enter__(self):
            return [FakePage(), FakePage()]

        def __exit__(self, exc_type, exc, tb):
            return False

    seen_langs = []

    def fake_image_to_string(_image, lang=None):
        seen_langs.append(lang)
        return "第 1 条 租金"

    fake_tesseract = SimpleNamespace(
        get_languages=lambda: ["eng", "chi_sim", "osd"],
        image_to_string=fake_image_to_string,
        TesseractNotFoundError=RuntimeError,
    )
    monkeypatch.setitem(sys.modules, "pytesseract", fake_tesseract)
    monkeypatch.setitem(
        sys.modules,
        "pypdfium2",
        SimpleNamespace(PdfDocument=lambda _p: FakePdf()),
    )

    text = parser._ocr_pdf(fake_file)
    assert text.count("第 1 条 租金") == 2
    assert seen_langs == ["chi_sim+eng", "chi_sim+eng"]


def test_ocr_language_falls_back_to_english(tmp_path, monkeypatch):
    from contractguard import parser

    fake_tesseract = SimpleNamespace(get_languages=lambda: ["eng", "osd"])
    monkeypatch.setitem(sys.modules, "pytesseract", fake_tesseract)
    assert parser._tesseract_languages() == "eng"


def test_ocr_missing_binary_is_actionable(tmp_path, monkeypatch):
    from contractguard import parser

    fake_file = tmp_path / "scan.pdf"
    fake_file.write_bytes(b"%PDF-1.4\n")

    class NotFoundError(Exception):
        pass

    def raise_not_found():
        raise NotFoundError("tesseract is not installed or it's not in your PATH")

    fake_tesseract = SimpleNamespace(
        get_languages=raise_not_found,
        TesseractNotFoundError=NotFoundError,
    )
    monkeypatch.setitem(sys.modules, "pytesseract", fake_tesseract)
    monkeypatch.setitem(sys.modules, "pypdfium2", SimpleNamespace())

    with pytest.raises(ValueError) as exc_info:
        parser._ocr_pdf(fake_file)
    assert "brew install tesseract" in str(exc_info.value) or "apt install" in str(exc_info.value)


def test_extract_nda():
    """Test extracting text from NDA sample."""
    text = extract_text(EXAMPLES_DIR / "sample_nda.txt")
    assert "NON-DISCLOSURE AGREEMENT" in text
    assert "Confidential Information" in text
