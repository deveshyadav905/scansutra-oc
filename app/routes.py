# app/routes.py

import os
import uuid
import shutil
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, JSONResponse
from app.job_manager import submit_job, get_job, cancel_job, JobStatus

router = APIRouter()

BASE_DIR = "jobs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

os.makedirs(BASE_DIR, exist_ok=True)


def _job_dir(job_id: str) -> str:
    path = os.path.join(BASE_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path


# ──────────────────────────────────────────────
# POST /api/ocr/
# ──────────────────────────────────────────────
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

    dir_id      = str(uuid.uuid4())
    job_dir     = _job_dir(dir_id)
    input_path  = os.path.join(job_dir, "input.pdf")
    output_path = os.path.join(job_dir, "output.pdf")

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(contents)

    job_id = submit_job(input_path, output_path, lang, job_dir)

    return JSONResponse(
        status_code=202,
        content={"job_id": job_id, "status": "queued"},
    )


# ──────────────────────────────────────────────
# GET /api/status/{job_id}
# ──────────────────────────────────────────────
@router.get("/status/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job_id,
        "status": job.status.value,
        "step":   job.step,
    }


# ──────────────────────────────────────────────
# GET /api/result/{job_id}
# ──────────────────────────────────────────────
@router.get("/result/{job_id}")
async def download_result(job_id: str):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")

    if job.status != JobStatus.DONE:
        raise HTTPException(status_code=404, detail="Result not ready yet.")

    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Output file missing.")

    # Read into memory first, then delete — avoids race condition
    async with aiofiles.open(job.output_path, "rb") as f:
        pdf_bytes = await f.read()

    shutil.rmtree(os.path.dirname(job.output_path), ignore_errors=True)
    cancel_job(job_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=searchable_output.pdf"},
    )


# ──────────────────────────────────────────────
# DELETE /api/job/{job_id}
# ──────────────────────────────────────────────
@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    job = get_job(job_id)
    if job and job.output_path:
        shutil.rmtree(os.path.dirname(job.output_path), ignore_errors=True)
    cancel_job(job_id)
    return {"job_id": job_id, "status": "cancelled"}