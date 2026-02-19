import os
import uuid
import shutil
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, JSONResponse
from celery.result import AsyncResult
from app.tasks import celery_app, run_ocr

router = APIRouter()

BASE_DIR = "jobs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
os.makedirs(BASE_DIR, exist_ok=True)

def _job_dir(job_id: str) -> str:
    path = os.path.join(BASE_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path

@router.post("/ocr/")
async def submit_ocr(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50 MB).")

    job_id  = str(uuid.uuid4())
    job_dir = _job_dir(job_id)

    input_path  = os.path.join(job_dir, "input.pdf")
    output_path = os.path.join(job_dir, "output.pdf")

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(contents)

    task = run_ocr.apply_async(
        args=[input_path, output_path, lang, job_dir],
        task_id=job_id,
    )

    return JSONResponse(
        status_code=202,
        content={"job_id": task.id, "status": "queued"},
    )

@router.get("/status/{job_id}")
async def job_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return {"job_id": job_id, "status": "queued"}
    if result.state == "STARTED":
        return {"job_id": job_id, "status": "processing", "step": "Initializing"}
    if result.state == "PROCESSING":
        meta = result.info or {}
        return {"job_id": job_id, "status": "processing", "step": meta.get("step", "Working")}
    if result.state == "SUCCESS":
        return {"job_id": job_id, "status": "done"}
    if result.state == "FAILURE":
        return JSONResponse(
            status_code=500,
            content={"job_id": job_id, "status": "failed", "error": str(result.info)},
        )
    return {"job_id": job_id, "status": result.state.lower()}

@router.get("/result/{job_id}")
async def download_result(job_id: str):
    result = AsyncResult(job_id, app=celery_app)

    if result.state != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not ready or job not found.")

    info = result.result or {}
    output_path = info.get("output_path")

    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file missing.")

    async with aiofiles.open(output_path, "rb") as f:
        pdf_bytes = await f.read()

    # Clean up job directory after reading into memory
    job_dir = os.path.join(BASE_DIR, job_id)
    shutil.rmtree(job_dir, ignore_errors=True)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=searchable_output.pdf"},
    )

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    result.revoke(terminate=True)
    job_dir = os.path.join(BASE_DIR, job_id)
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir, ignore_errors=True)
    return {"job_id": job_id, "status": "cancelled"}