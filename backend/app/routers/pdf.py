from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import pdf_extract

router = APIRouter(prefix="/api", tags=["pdf"])


@router.post("/extract-pdf")
def extract_pdf(file: UploadFile | None = File(default=None)) -> dict:
    if file is None:
        raise HTTPException(status_code=422, detail="No file uploaded. Attach a PDF file.")
    if file.content_type and file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=422, detail="File must be a PDF.")
    data = file.file.read()
    if len(data) > pdf_extract.MAX_BYTES:
        raise HTTPException(status_code=413, detail="PDF is over 5 MB. Use a smaller file.")
    return pdf_extract.extract_pdf_text(data)
