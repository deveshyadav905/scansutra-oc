# app/job_manager.py

import os
import time
import uuid
import shutil
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Dict
from dataclasses import dataclass, field
from enum import Enum
from app.config import MAX_PARALLEL_JOBS
from app.logger import get_logger

log = get_logger(__name__)


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
    job_dir:     str       = ""
    error:       str       = ""
    page_count:  int       = 0
    created_at:  float     = field(default_factory=time.time)


# ── Global state ───────────────────────────────────────────────────────────────
_jobs: Dict[str, Job] = {}

_executor = ProcessPoolExecutor(max_workers=MAX_PARALLEL_JOBS)

log.info(f"ProcessPoolExecutor initialized | max_parallel_jobs={MAX_PARALLEL_JOBS}")


def _safe_cleanup(job_dir: str, label: str = ""):
    if job_dir and os.path.exists(job_dir):
        shutil.rmtree(job_dir, ignore_errors=True)
        log.info(f"Cleaned up job dir ({label}) | path={job_dir}")


# ── Worker — runs in a subprocess ─────────────────────────────────────────────
def _ocr_worker(input_path: str, output_path: str, lang: str, job_dir: str):
    from app.ocr_engine import process_pdf
    from app.pdf_utils import merge_pdfs, cleanup as cleanup_temp_files
    from app.logger import get_logger

    log = get_logger("ocr_worker")
    log.info(f"Worker started | lang={lang} | input={input_path}")

    pdf_files = []
    try:
        # ✅ FIX BUG 2: If server restarted and deleted this dir, fail immediately
        # instead of crashing page by page with FileNotFoundError
        if not os.path.exists(job_dir):
            raise RuntimeError(f"Job directory no longer exists — server may have restarted.")

        pdf_files, texts = process_pdf(input_path, lang=lang, output_dir=job_dir)
        log.info(f"OCR complete | pages={len(texts)} | merging...")

        merge_pdfs(pdf_files, output_path)
        log.info(f"Job complete | output={output_path}")
        return output_path, len(texts)

    except Exception:
        log.error(f"Worker failed | input={input_path}", exc_info=True)
        _safe_cleanup(job_dir, "worker exception")
        raise

    finally:
        cleanup_temp_files(pdf_files)
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
                log.debug(f"Input deleted | path={input_path}")
            except OSError as e:
                log.warning(f"Could not delete input | error={e}")


# ── Public API ─────────────────────────────────────────────────────────────────
def submit_job(input_path: str, output_path: str, lang: str, job_dir: str) -> str:
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        step="Starting OCR",
        job_dir=job_dir,
        output_path=output_path,
    )
    _jobs[job_id] = job
    log.info(f"Job queued | job_id={job_id}")

    future: Future = _executor.submit(_ocr_worker, input_path, output_path, lang, job_dir)

    def _on_done(fut: Future):
        # ✅ FIX BUG 3: After server restart _jobs is empty — the subprocess
        # callback fires into a new process that doesn't know this job.
        # Guard with .get() instead of direct key access to prevent KeyError.
        job = _jobs.get(job_id)
        if job is None:
            log.warning(
                f"_on_done callback for unknown job_id={job_id} — "
                f"server likely restarted while job was running. Cleaning up."
            )
            # Still clean up the folder even though we lost track of the job
            _safe_cleanup(job_dir, "orphaned after restart")
            return

        if fut.cancelled():
            job.status = JobStatus.FAILED
            job.error  = "Job was cancelled."
            _safe_cleanup(job_dir, "cancelled")
            log.warning(f"Job cancelled | job_id={job_id}")
            return

        exc = fut.exception()
        if exc:
            job.status = JobStatus.FAILED
            job.error  = str(exc)
            _safe_cleanup(job_dir, "worker exception callback")
            log.error(f"Job failed | job_id={job_id} | error={exc}")
        else:
            result_path, page_count = fut.result()
            job.status      = JobStatus.DONE
            job.step        = "Done"
            job.output_path = result_path
            job.page_count  = page_count
            log.info(f"Job done | job_id={job_id} | pages={page_count}")

    future.add_done_callback(_on_done)
    return job_id


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def cancel_job(job_id: str):
    _jobs.pop(job_id, None)


def cleanup_stale_jobs(max_age_seconds: int = 3600):
    """Remove jobs older than max_age_seconds. Called periodically from main.py."""
    now = time.time()
    stale = [
        job_id for job_id, job in list(_jobs.items())
        if now - job.created_at > max_age_seconds
    ]
    for job_id in stale:
        job = _jobs[job_id]
        _safe_cleanup(job.job_dir, f"stale job_id={job_id}")
        cancel_job(job_id)
        log.info(f"Stale job removed | job_id={job_id}")
    return len(stale)


def shutdown():
    log.info("Shutting down — cleaning up pending jobs...")
    for job_id, job in list(_jobs.items()):
        if job.status in (JobStatus.QUEUED, JobStatus.PROCESSING):
            _safe_cleanup(job.job_dir, f"shutdown job_id={job_id}")
    _jobs.clear()
    _executor.shutdown(wait=False, cancel_futures=True)
    log.info("ProcessPoolExecutor shut down.")