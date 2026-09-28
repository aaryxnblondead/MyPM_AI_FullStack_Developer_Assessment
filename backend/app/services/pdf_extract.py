"""PDF text extraction for pasted-resume alternative. File is never stored."""
import io
import re

from fastapi import HTTPException

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 10
MIN_CHARS = 50


def extract_pdf_text(data: bytes) -> dict:
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="PDF is over 5 MB. Use a smaller file.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="File is not a PDF. Upload a real PDF file.")
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise HTTPException(status_code=500, detail="PDF support is not installed. Try again.") from e
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as e:
        raise HTTPException(status_code=422, detail="PDF is corrupt and cannot be read.") from e
    if getattr(reader, "is_encrypted", False):
        raise HTTPException(status_code=422, detail="Encrypted PDFs are not supported.")
    pages = list(reader.pages)
    if len(pages) > MAX_PAGES:
        raise HTTPException(
            status_code=422,
            detail=f"PDF has {len(pages)} pages. Keep it to {MAX_PAGES} pages or fewer.",
        )
    parts = []
    for p in pages:
        try:
            parts.append(p.extract_text() or "")
        except Exception as e:
            raise HTTPException(status_code=422, detail="PDF text could not be read.") from e
    text = re.sub(r"[ \t]+", " ", "\n".join(parts))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < MIN_CHARS:
        raise HTTPException(
            status_code=422,
            detail="PDF has no readable text. Scanned images need OCR, which is not supported.",
        )
    return {"text": text, "pages": len(pages), "chars": len(text)}
