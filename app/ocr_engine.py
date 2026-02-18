# app/ocr_engine.py

from pdf2image import convert_from_path
import pytesseract
from app.preprocessing import preprocess

def process_pdf(input_path, lang="eng", dpi=400):
    pages = convert_from_path(input_path, dpi=dpi)

    pdf_files = []
    extracted_text = []

    for i, page in enumerate(pages):
        clean_page = preprocess(page)

        text = pytesseract.image_to_string(
            clean_page,
            lang=lang,
            config="--oem 3 --psm 6",
        )
        extracted_text.append(text)

        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            clean_page,
            lang=lang,
            extension="pdf",
        )

        temp_pdf = f"outputs/temp_page_{i}.pdf"
        with open(temp_pdf, "wb") as f:
            f.write(pdf_bytes)

        pdf_files.append(temp_pdf)

    return pdf_files, extracted_text
