# app/routes.py

import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, JSONResponse

from app.job_manager import submit_job, get_job, cancel_job, JobStatus, _safe_cleanup
from app.logger import get_logger

log = get_logger(__name__)

router = APIRouter()

BASE_DIR = "jobs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

os.makedirs(BASE_DIR, exist_ok=True)


def _job_dir(dir_id: str) -> str:
    path = os.path.join(BASE_DIR, dir_id)
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
    log.info(f"Upload received | filename={file.filename} | lang={lang}")

    if not file.filename.lower().endswith(".pdf"):
        log.warning(f"Rejected non-PDF | filename={file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()
    size_kb = len(contents) // 1024

    if len(contents) == 0:
        log.warning("Rejected empty file")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_FILE_SIZE:
        log.warning(f"Rejected oversized file | size={size_kb}KB")
        raise HTTPException(status_code=400, detail="File too large (max 50 MB).")

    dir_id      = str(uuid.uuid4())
    job_dir     = _job_dir(dir_id)
    input_path  = os.path.join(job_dir, "input.pdf")
    output_path = os.path.join(job_dir, "output.pdf")

    try:
        async with aiofiles.open(input_path, "wb") as f:
            await f.write(contents)
    except Exception as e:
        # ✅ FAILURE PATH 4: file write failed — clean up the job dir immediately
        _safe_cleanup(job_dir, "upload write failed")
        log.error(f"Failed to save uploaded file | error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    job_id = submit_job(input_path, output_path, lang, job_dir)
    log.info(f"Job submitted | job_id={job_id} | lang={lang} | size={size_kb}KB")

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
        log.warning(f"Status check for unknown job | job_id={job_id}")
        raise HTTPException(status_code=404, detail="Job not found.")

    log.debug(f"Status | job_id={job_id} | status={job.status.value} | step={job.step}")
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
        log.warning(f"Result fetch for unknown job | job_id={job_id}")
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status == JobStatus.FAILED:
        # ✅ FAILURE PATH 5: user fetches result of a failed job
        # job_dir already cleaned by _on_done, but ensure it's gone
        _safe_cleanup(job.job_dir, "failed job result fetch")
        cancel_job(job_id)  # remove from memory too
        log.error(f"Result fetch for failed job | job_id={job_id} | error={job.error}")
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")

    if job.status != JobStatus.DONE:
        log.debug(f"Result not ready | job_id={job_id} | status={job.status.value}")
        raise HTTPException(status_code=404, detail="Result not ready yet.")

    if not job.output_path or not os.path.exists(job.output_path):
        # ✅ FAILURE PATH 6: output file missing despite DONE status
        _safe_cleanup(job.job_dir, "output missing")
        cancel_job(job_id)
        log.error(f"Output file missing | job_id={job_id} | path={job.output_path}")
        raise HTTPException(status_code=404, detail="Output file missing.")

    try:
        async with aiofiles.open(job.output_path, "rb") as f:
            pdf_bytes = await f.read()
    except Exception as e:
        # ✅ FAILURE PATH 7: read failed after job completed
        _safe_cleanup(job.job_dir, "result read failed")
        cancel_job(job_id)
        log.error(f"Failed to read output file | job_id={job_id} | error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read output file.")

    # ✅ SUCCESS: clean up job dir now that file is fully in memory
    _safe_cleanup(job.job_dir, "success delivery")
    cancel_job(job_id)

    log.info(f"Result delivered | job_id={job_id} | pages={job.page_count} | size={len(pdf_bytes)//1024}KB")

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
    if job:
        _safe_cleanup(job.job_dir, "manual delete")
    cancel_job(job_id)
    log.info(f"Job deleted | job_id={job_id}")
    return {"job_id": job_id, "status": "cancelled"}


# ──────────────────────────────────────────────
# POST /api/job/{job_id}/cancel
# ✅ sendBeacon only supports POST — this is the
#    unload-safe cancel endpoint called on tab close / refresh
# ──────────────────────────────────────────────
@router.post("/job/{job_id}/cancel")
async def cancel_job_post(job_id: str):
    job = get_job(job_id)
    if job:
        _safe_cleanup(job.job_dir, "beacon cancel")
    cancel_job(job_id)
    log.info(f"Job beacon-cancelled | job_id={job_id}")
    return {"job_id": job_id, "status": "cancelled"}