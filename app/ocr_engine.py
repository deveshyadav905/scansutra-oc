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
        del page  # free memory

        # Get text
        text = pytesseract.image_to_string(
            clean_page, lang=lang, config="--oem 3 --psm 6"
        )

        # Create searchable PDF layer
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            clean_page, lang=lang, extension="pdf"
        )

        temp_pdf = os.path.join(output_dir, f"temp_page_{i}.pdf")
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes)

        return i, temp_pdf, text

    except Exception as e:
        raise RuntimeError(f"Failed on page {i}: {e}") from e

def process_pdf(input_path: str, lang: str = "eng", dpi: int = 300, output_dir: str = None):
    if output_dir is None:
        raise ValueError("output_dir must be explicitly provided.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    pages = convert_from_path(input_path, dpi=dpi)

    if not pages:
        raise ValueError("PDF has no pages or could not be read.")

    tasks = [(i, page, lang, output_dir) for i, page in enumerate(pages)]
    results = {}
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_page, task): task[0] for task in tasks}
        for future in as_completed(futures):
            page_index = futures[future]
            try:
                i, temp_pdf, text = future.result()
                results[i] = (temp_pdf, text)
            except Exception as e:
                errors.append(str(e))

    if errors:
        raise RuntimeError(f"OCR failed on {len(errors)} page(s): {'; '.join(errors)}")

    pdf_files = [results[i][0] for i in range(len(pages))]
    extracted_text = [results[i][1] for i in range(len(pages))]

    return pdf_files, extracted_text