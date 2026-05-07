"""Document parsing: extract text from PDF, DOCX, TXT, and image files."""

from __future__ import annotations

from pathlib import Path


def extract_text(file_path: str | Path) -> str:
    """Extract text content from a document file.

    Supports: .pdf, .docx, .txt, .md, .rtf
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix == ".docx":
        return _extract_docx(path)
    elif suffix in (".txt", ".md", ".rtf"):
        return path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Supported: .pdf, .docx, .txt, .md, .rtf"
        )


def _extract_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF files: pip install pdfplumber")

    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        raise ValueError(
            f"Could not extract text from PDF: {path}. "
            "The PDF may be scanned or image-based. OCR support is not available yet; "
            "please use a text-based PDF, DOCX, TXT, MD, or RTF file."
        )

    return "\n\n".join(text_parts)


def _extract_docx(path: Path) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX files: pip install python-docx")

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
