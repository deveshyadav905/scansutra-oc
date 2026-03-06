import os

MAX_PARALLEL_JOBS = int(os.getenv("MAX_PARALLEL_JOBS", 2))
MAX_WORKERS = int(os.getenv("OCR_MAX_WORKERS", 4))
DEFAULT_DPI  = int(os.getenv("OCR_DPI", 200))