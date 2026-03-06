# app/ocr_engine.py

import os
import time
import pytesseract
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf2image import convert_from_path
from PIL import Image
from app.config import DEFAULT_DPI,MAX_WORKERS
from app.preprocessing import preprocess
from app.logger import get_logger

log = get_logger(__name__)

MAX_WORKERS = int(os.getenv("OCR_MAX_WORKERS", 4))


def _set_dpi(image: Image.Image, dpi: int) -> Image.Image:
    """Stamp DPI onto preprocessed image — prevents Tesseract 'Invalid resolution 0 dpi' error."""
    image.info["dpi"] = (dpi, dpi)
    return image


def _process_page(args):
    i, page, lang, output_dir, dpi = args
    temp_pdf = os.path.join(output_dir, f"temp_page_{i}.pdf")

    # ✅ If job was cancelled and dir deleted — exit silently, not with a noisy error
    if not os.path.exists(output_dir):
        raise RuntimeError("__CANCELLED__")

    try:
        start = time.perf_counter()
        clean_page = preprocess(page)
        del page

        # ✅ FIX 1: Pass dpi as argument — subprocess cannot read module globals from parent
        clean_page = _set_dpi(clean_page, dpi)

        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            clean_page, lang=lang, extension="pdf", config="--oem 3 --psm 6"
        )
        text = pytesseract.image_to_string(
            clean_page, lang=lang, config="--oem 3 --psm 6"
        )

        # Check again just before writing
        if not os.path.exists(output_dir):
            raise RuntimeError("__CANCELLED__")

        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes)

        del clean_page
        elapsed = (time.perf_counter() - start) * 1000
        log.debug(f"Page {i} done | {elapsed:.0f}ms | chars={len(text.strip())}")
        return i, temp_pdf, text

    except RuntimeError as e:
        if "__CANCELLED__" in str(e):
            raise  # propagate silently — handled in process_pdf
        if os.path.exists(temp_pdf):
            try: os.remove(temp_pdf)
            except OSError: pass
        log.error(f"Page {i} failed | error={e}", exc_info=True)
        raise RuntimeError(f"Failed on page {i}: {e}") from e

    except Exception as e:
        if os.path.exists(temp_pdf):
            try: os.remove(temp_pdf)
            except OSError: pass
        log.error(f"Page {i} failed | error={e}", exc_info=True)
        raise RuntimeError(f"Failed on page {i}: {e}") from e


def process_pdf(input_path: str, lang: str = "eng", dpi: int = 200, output_dir: str = None):
    if output_dir is None:
        raise ValueError("output_dir must be explicitly provided.")

    os.makedirs(output_dir, exist_ok=True)

    log.info(f"Converting PDF → images | dpi={dpi} | path={input_path}")
    t0 = time.perf_counter()

    try:
        pages = convert_from_path(
            input_path,
            dpi=dpi,
            use_pdftocairo=True,
            thread_count=min(MAX_WORKERS, 4),
        )
    except Exception as e:
        log.error(f"PDF rendering failed | error={e}", exc_info=True)
        raise

    if not pages:
        raise ValueError("PDF has no pages or could not be read.")

    log.info(f"PDF rendered | pages={len(pages)} | {(time.perf_counter()-t0)*1000:.0f}ms")

    # ✅ FIX 1: Pass dpi explicitly into each task — not read from globals
    tasks = [(i, page, lang, output_dir, dpi) for i, page in enumerate(pages)]
    results = {}
    errors = []
    cancelled = False

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_page, task): task[0] for task in tasks}
        for future in as_completed(futures):
            try:
                i, temp_pdf, text = future.result()
                results[i] = (temp_pdf, text)
            except RuntimeError as e:
                if "__CANCELLED__" in str(e):
                    # ✅ FIX 2: Job was cancelled — stop silently, don't spam error logs
                    cancelled = True
                else:
                    errors.append(str(e))

    if cancelled:
        # Clean up any pages that did complete before cancellation
        for i, (temp_pdf, _) in results.items():
            if os.path.exists(temp_pdf):
                try: os.remove(temp_pdf)
                except OSError: pass
        log.info("Job was cancelled — worker exiting cleanly.")
        raise RuntimeError("Job was cancelled.")

    if errors:
        for i, (temp_pdf, _) in results.items():
            if os.path.exists(temp_pdf):
                try: os.remove(temp_pdf)
                except OSError: pass
        log.error(f"OCR failed on {len(errors)} page(s)")
        raise RuntimeError(f"OCR failed on {len(errors)} page(s): {'; '.join(errors)}")

    total = (time.perf_counter() - t0) * 1000
    log.info(f"All pages OCR'd | pages={len(pages)} | total={total:.0f}ms")

    pdf_files      = [results[i][0] for i in range(len(pages))]
    extracted_text = [results[i][1] for i in range(len(pages))]

    return pdf_files, extracted_text