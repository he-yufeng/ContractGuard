"""Document parsing: extract text from PDF, DOCX, TXT, and image files."""

from __future__ import annotations

from pathlib import Path

# Below this many characters of embedded text across the whole PDF we treat the
# document as image-only and try OCR instead of trusting the stray header or
# watermark line some scans carry.
_IMAGE_ONLY_TEXT_THRESHOLD = 50


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
    """Extract text from a PDF file, falling back to OCR for image-only scans."""
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

    text = "\n\n".join(text_parts)
    if len(text.strip()) >= _IMAGE_ONLY_TEXT_THRESHOLD:
        return text

    # No (or only trace amounts of) embedded text: this is a scanned PDF.
    return _ocr_pdf(path)


def _ocr_guidance(path: Path) -> str:
    return (
        f"Could not extract text from PDF: {path}. "
        "The PDF appears to be a scan or photo of a document. OCR can read it, "
        "but it needs two things installed: the Python side (`pip install "
        '"contractguard[ocr]"`) and the Tesseract engine itself '
        "(macOS: `brew install tesseract tesseract-lang`; Debian/Ubuntu: "
        "`apt install tesseract-ocr tesseract-ocr-chi-sim`)."
    )


def _tesseract_languages() -> str:
    """Pick the OCR language set: Chinese + English when the language pack
    exists, English otherwise. Contracts in this project's scope are mostly
    Chinese or bilingual, and asking for a missing pack fails the whole run."""
    import pytesseract

    available = set(pytesseract.get_languages())
    if "chi_sim" in available:
        return "chi_sim+eng"
    return "eng"


def _ocr_pdf(path: Path) -> str:
    """OCR an image-only PDF: render each page at 300 dpi and read it.

    pypdfium2 renders without any system dependency; pytesseract drives the
    Tesseract binary, which is the one piece the user must install themselves.
    """
    try:
        import pytesseract
    except ImportError:
        raise ValueError(_ocr_guidance(path) + " (pytesseract is not installed.)")
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ValueError(_ocr_guidance(path) + " (pypdfium2 is not installed.)")

    try:
        languages = _tesseract_languages()
    except pytesseract.TesseractNotFoundError:
        raise ValueError(_ocr_guidance(path) + " (the tesseract binary was not found on PATH.)")

    text_parts: list[str] = []
    with pdfium.PdfDocument(str(path)) as pdf:
        for page in pdf:
            image = page.render(scale=300 / 72).to_pil()
            page_text = pytesseract.image_to_string(image, lang=languages)
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

    if not text_parts:
        raise ValueError(
            f"OCR could not read any text from {path} either. "
            "The scan may be too low-resolution, rotated, or handwritten."
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
