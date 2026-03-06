# app/pdf_utils.py

import os
from pypdf import PdfWriter, PdfReader
from app.logger import get_logger

log = get_logger(__name__)


def merge_pdfs(pdf_files, output_path):
    if not pdf_files:
        raise ValueError("No PDF pages to merge.")

    log.info(f"Merging {len(pdf_files)} page(s) → {output_path}")
    writer = PdfWriter()
    try:
        for pdf in pdf_files:
            if not os.path.exists(pdf):
                raise FileNotFoundError(f"Temp page PDF missing: {pdf}")
            reader = PdfReader(pdf)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        log.info(f"Merge complete | output={output_path}")
    finally:
        writer.close()


def cleanup(files):
    removed = 0
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
                removed += 1
        except OSError as e:
            log.warning(f"Could not delete temp file | path={f} | error={e}")
    log.debug(f"Cleanup done | removed={removed} file(s)")