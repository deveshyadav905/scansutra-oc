import os
from pypdf import PdfWriter, PdfReader

def merge_pdfs(pdf_files, output_path):
    if not pdf_files:
        raise ValueError("No PDF pages to merge.")

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
    finally:
        writer.close()

def cleanup(files):
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError:
            pass