# 📄 ScanSutra OCR

> Convert scanned PDFs into fully searchable PDFs using **FastAPI + Tesseract OCR**.

ScanSutra OCR is a lightweight, high-performance OCR web application. It transforms non-searchable scanned documents into searchable PDFs using **async background processing** via Python's built-in `ProcessPoolExecutor` — no Redis, no Celery, no extra services required.

---

## ✅ Features

- 📤 Upload scanned PDF (up to 50MB)
- 🌐 Select OCR language — English / Hindi / Hindi + English
- 🔍 Convert scanned PDF to fully searchable PDF
- ⚡ Non-blocking background processing (ProcessPoolExecutor)
- 👁 Preview processed PDF in browser
- ⬇ Download searchable output
- 🧠 OpenCV image preprocessing for better accuracy
- 🛡 File type + size validation
- 🧹 Automatic temporary file cleanup
- 🚀 Multiple users handled simultaneously

---

## 🏗 Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| OCR Engine | Tesseract OCR |
| Image Processing | OpenCV |
| PDF Rendering | pdf2image + poppler |
| PDF Merging | pypdf |
| Parallelism | ProcessPoolExecutor (built-in) |
| Package Manager | uv |
| Frontend | HTML / CSS / Vanilla JS |

---

## 📂 Project Structure

```
scansutra/
│
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── README.md
│
└── app/
    ├── __init__.py
    ├── routes.py            # API endpoints
    ├── job_manager.py       # Process pool job queue (replaces Celery)
    ├── ocr_engine.py        # Tesseract OCR logic (parallel pages)
    ├── preprocessing.py     # OpenCV image cleanup
    ├── pdf_utils.py         # PDF merge + cleanup
    └── static/
        └── index.html       # Frontend UI

jobs/                        # Auto-created — one folder per upload
└── {uuid}/
    ├── input.pdf            # Uploaded file (deleted after OCR)
    ├── temp_page_N.pdf      # Per-page output (deleted after merge)
    └── output.pdf           # Final result (deleted after download)
```

---

## ⚙ Installation

### 1. Clone & enter project

```bash
git clone https://github.com/yourusername/scansutra-ocr.git
cd scansutra-ocr
```

### 2. Install `uv` (fast Python package manager)

```bash
# Linux / macOS
curl -Lsf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> `uv` is 10–100x faster than `pip`. It replaces both `pip` and `venv`.

### 3. Create virtual environment with Python 3.12

```bash
uv venv --python 3.12
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 4. Install Python dependencies

```bash
uv pip install -r requirements.txt
```

### 5. Install system dependencies

**Ubuntu / Debian:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
brew install tesseract-lang      # for Hindi support
```

**Windows:**
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases

---

## ▶ Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open browser:
```
http://localhost:8000
```

That's it — **one command, no background services needed**.

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ocr/` | Upload PDF, returns `job_id` |
| GET | `/api/status/{job_id}` | Poll job progress |
| GET | `/api/result/{job_id}` | Download finished PDF |
| DELETE | `/api/job/{job_id}` | Cancel / cleanup job |

### Example flow

```bash
# 1. Submit
curl -X POST http://localhost:8000/api/ocr/ \
  -F "file=@scan.pdf" \
  -F "lang=eng"
# → {"job_id": "abc-123", "status": "queued"}

# 2. Poll
curl http://localhost:8000/api/status/abc-123
# → {"status": "processing", "step": "Starting OCR"}
# → {"status": "done"}

# 3. Download
curl http://localhost:8000/api/result/abc-123 -o output.pdf
```

---

## ⚡ Speed Optimizations Applied

| Optimization | Impact |
|---|---|
| DPI lowered 300 → 200 | ~2x faster PDF-to-image conversion |
| `use_pdftocairo=True` | Faster rendering than default pdftoppm |
| `thread_count` in pdf2image | Parallel page rendering |
| `ThreadPoolExecutor` per job | All pages OCR'd in parallel |
| `ProcessPoolExecutor` for jobs | Multiple users processed simultaneously |
| Single tesseract call per page | Removed duplicate OCR call |
| `COLOR_RGB2GRAY` (correct) | Accurate grayscale → better OCR results |

### DPI guide

| DPI | Speed | Quality | Use for |
|---|---|---|---|
| 150 | ⚡⚡⚡ Fast | ⭐⭐ OK | Large files, quick preview |
| 200 | ⚡⚡ Good | ⭐⭐⭐ Good | **Default — best balance** |
| 300 | ⚡ Slow | ⭐⭐⭐⭐ High | Legal / archival documents |

Change DPI via env var:
```bash
OCR_DPI=150 uvicorn main:app --reload   # faster
OCR_DPI=300 uvicorn main:app --reload   # higher quality
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OCR_MAX_WORKERS` | `4` | Threads per job for page-level parallelism |
| `MAX_PARALLEL_JOBS` | `2` | Max simultaneous OCR jobs |
| `OCR_DPI` | `200` | DPI for PDF-to-image rendering |

---

## 📦 uv Cheat Sheet

```bash
# Install uv
curl -Lsf https://astral.sh/uv/install.sh | sh

# Create venv
uv venv --python 3.12

# Activate
source .venv/bin/activate

# Install from requirements.txt
uv pip install -r requirements.txt

# Add a new package
uv pip install some-package

# Freeze current packages
uv pip freeze > requirements.txt

# Check uv version
uv --version
```

---

## 🛡 Security

- PDF-only file validation (filename check)
- 50MB file size limit
- UUID-based isolated job directories
- Automatic cleanup after download
- No user data retained after processing

---

## 📈 Use Cases

- Government document digitization
- Hindi / multilingual document OCR
- Legal and archival document scanning
- Newspaper and book digitization
- High-volume OCR processing pipeline

---

## 🧠 Future Improvements

- [ ] WebSocket real-time progress updates
- [ ] Multi-file batch upload
- [ ] OCR history with database storage
- [ ] Cloud storage (S3) integration
- [ ] Docker one-click deployment
- [ ] API key support for SaaS model
- [ ] User authentication + JWT

---

## 👨‍💻 Author

**Devesh Yadav**  
Python Backend Developer | OCR & Automation Specialist

---

## 📜 License

MIT License