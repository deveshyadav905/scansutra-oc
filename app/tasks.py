import os
import shutil
from celery import Celery
from app.ocr_engine import process_pdf
from app.pdf_utils import merge_pdfs, cleanup as cleanup_temp_files

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "scansutra",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

@celery_app.task(bind=True, name="tasks.run_ocr")
def run_ocr(self, input_path: str, output_path: str, lang: str, job_dir: str):
    pdf_files = []
    try:
        self.update_state(state="PROCESSING", meta={"step": "Starting OCR"})

        # Process PDF (returns list of temp pdf pages and extracted text)
        pdf_files, texts = process_pdf(input_path, lang=lang, output_dir=job_dir)

        self.update_state(state="PROCESSING", meta={"step": "Merging pages"})
        merge_pdfs(pdf_files, output_path)

        return {
            "status": "done",
            "output_path": output_path,
            "page_count": len(texts),
        }

    except Exception as exc:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
        raise exc

    finally:
        cleanup_temp_files(pdf_files)
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass