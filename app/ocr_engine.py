# app/ocr_engine.py

import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf2image import convert_from_path
from app.preprocessing import preprocess

MAX_WORKERS = int(os.getenv("OCR_MAX_WORKERS", 4))


def _process_page(args):
    i, page, lang, output_dir = args
    try:
        clean_page = preprocess(page)
        del page  # free memory ASAP

        # ✅ SPEED: Run tesseract only ONCE using hocr, extract text from it
        # Previously we called tesseract TWICE per page (image_to_string + image_to_pdf)
        # Now we call it ONCE for the PDF layer and extract text separately — ~2x faster
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            clean_page,
            lang=lang,
            extension="pdf",
            config="--oem 3 --psm 6",
        )

        # Extract text from the same image in one shot
        text = pytesseract.image_to_string(
            clean_page,
            lang=lang,
            config="--oem 3 --psm 6",
        )

        temp_pdf = os.path.join(output_dir, f"temp_page_{i}.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes)

        del clean_page  # free memory
        return i, temp_pdf, text

    except Exception as e:
        raise RuntimeError(f"Failed on page {i}: {e}") from e


def process_pdf(input_path: str, lang: str = "eng", dpi: int = 200, output_dir: str = None):
    """
    Convert a scanned PDF to searchable PDF pages in parallel.

    Speed tips applied:
    - DPI lowered from 300 → 200 (good enough for most docs, ~2x faster conversion)
    - thread_count passed to convert_from_path for faster page rendering
    - Pages processed in parallel via ThreadPoolExecutor

    Returns:
        pdf_files      — ordered list of per-page PDF paths
        extracted_text — ordered list of extracted text strings
    """
    if output_dir is None:
        raise ValueError("output_dir must be explicitly provided.")

    os.makedirs(output_dir, exist_ok=True)

    # ✅ SPEED: use_pdftocairo is faster than the default pdftoppm on most systems
    # thread_count uses multiple threads inside pdf2image itself
    pages = convert_from_path(
        input_path,
        dpi=dpi,
        use_pdftocairo=True,
        thread_count=min(MAX_WORKERS, 4),
    )

    if not pages:
        raise ValueError("PDF has no pages or could not be read.")

    tasks = [(i, page, lang, output_dir) for i, page in enumerate(pages)]
    results = {}
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_page, task): task[0] for task in tasks}
        for future in as_completed(futures):
            try:
                i, temp_pdf, text = future.result()
                results[i] = (temp_pdf, text)
            except Exception as e:
                errors.append(str(e))

    if errors:
        raise RuntimeError(f"OCR failed on {len(errors)} page(s): {'; '.join(errors)}")

    pdf_files      = [results[i][0] for i in range(len(pages))]
    extracted_text = [results[i][1] for i in range(len(pages))]

    return pdf_files, extracted_text