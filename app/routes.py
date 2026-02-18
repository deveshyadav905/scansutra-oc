import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.ocr_engine import process_pdf
from app.pdf_utils import merge_pdfs, cleanup as cleanup_temp_files


router = APIRouter()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB limit

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/ocr/")
async def ocr_pdf(file: UploadFile = File(...), lang: str = "eng"):
    print("OCR request received")
    print("Language:", lang)

    # ✅ Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # ✅ Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (Max 20MB).")

    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{unique_id}.pdf")
    output_path = os.path.join(OUTPUT_DIR, f"{unique_id}_output.pdf")

    try:
        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(contents)

        # Process OCR
        pdf_files, texts = process_pdf(input_path, lang=lang)

        # Merge PDFs
        merge_pdfs(pdf_files, output_path)

        # Cleanup temp page PDFs
        cleanup_temp_files(pdf_files)

        # Remove original upload to save storage
        os.remove(input_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="searchable_output.pdf",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/cleanup")
async def cleanup_dirs():
    """Clears uploads and outputs directories on page refresh/unload."""
    for folder in [UPLOAD_DIR, OUTPUT_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)
    return {"status": "cleaned"}