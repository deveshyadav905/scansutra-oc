# app/job_manager.py
"""
Zero-dependency job queue using ProcessPoolExecutor.
Replaces Celery + Redis — no extra services needed.

Each OCR job runs in a separate process (true parallelism, bypasses GIL).
Job state is tracked in a simple in-memory dict.
"""

import os
import uuid
import shutil
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Dict
from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    QUEUED     = "queued"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


@dataclass
class Job:
    job_id:      str
    status:      JobStatus = JobStatus.QUEUED
    step:        str       = ""
    output_path: str       = ""
    error:       str       = ""
    page_count:  int       = 0


# ── Global state ───────────────────────────────────────────────────────────────
_jobs: Dict[str, Job] = {}

MAX_PARALLEL_JOBS = int(os.getenv("MAX_PARALLEL_JOBS", 2))
_executor = ProcessPoolExecutor(max_workers=MAX_PARALLEL_JOBS)


# ── Worker — runs in a subprocess ─────────────────────────────────────────────
def _ocr_worker(input_path: str, output_path: str, lang: str, job_dir: str):
    """Runs in a separate process. Returns (output_path, page_count)."""
    from app.ocr_engine import process_pdf
    from app.pdf_utils import merge_pdfs, cleanup as cleanup_temp_files

    try:
        pdf_files, texts = process_pdf(input_path, lang=lang, output_dir=job_dir)
        merge_pdfs(pdf_files, output_path)
        cleanup_temp_files(pdf_files)
        return output_path, len(texts)
    except Exception:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
        raise
    finally:
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass


# ── Public API ─────────────────────────────────────────────────────────────────
def submit_job(input_path: str, output_path: str, lang: str, job_dir: str) -> str:
    """Submit an OCR job. Returns job_id immediately."""
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, status=JobStatus.PROCESSING, step="Starting OCR")
    _jobs[job_id] = job

    future: Future = _executor.submit(_ocr_worker, input_path, output_path, lang, job_dir)

    def _on_done(fut: Future):
        if fut.cancelled():
            _jobs[job_id].status = JobStatus.FAILED
            _jobs[job_id].error  = "Job was cancelled."
            return
        exc = fut.exception()
        if exc:
            _jobs[job_id].status = JobStatus.FAILED
            _jobs[job_id].error  = str(exc)
        else:
            result_path, page_count  = fut.result()
            _jobs[job_id].status     = JobStatus.DONE
            _jobs[job_id].step       = "Done"
            _jobs[job_id].output_path = result_path
            _jobs[job_id].page_count  = page_count

    future.add_done_callback(_on_done)
    return job_id


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def cancel_job(job_id: str):
    _jobs.pop(job_id, None)


def shutdown():
    """Call on app shutdown to clean up worker processes."""
    _executor.shutdown(wait=False, cancel_futures=True)