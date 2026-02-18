from PyPDF2 import PdfMerger
import os

def merge_pdfs(pdf_files, output_path):
    merger = PdfMerger()

    for pdf in pdf_files:
        merger.append(pdf)

    merger.write(output_path)
    merger.close()

def cleanup(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)
