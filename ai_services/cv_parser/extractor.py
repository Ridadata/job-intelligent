"""CV text extraction from PDF and DOCX files.

Uses PyPDF2 for PDF and python-docx for DOCX.
File size limit: 5 MB.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text string.

    Raises:
        ValueError: If the file exceeds the size limit.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE} byte limit")

    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extract raw text from a DOCX file.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        Extracted text string.

    Raises:
        ValueError: If the file exceeds the size limit.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE} byte limit")

    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(file_path: str) -> str:
    """Extract text from a CV file (PDF or DOCX).

    Args:
        file_path: Path to the CV file.

    Returns:
        Extracted text string.

    Raises:
        ValueError: If the file type is unsupported.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Accepted: .pdf, .docx")
