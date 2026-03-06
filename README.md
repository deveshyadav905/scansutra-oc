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
- 🧠 OpenCV image preprocessing for better OCR accuracy
- 🛡 File type + size validation
- 🧹 Automatic file cleanup on success, failure, cancel and refresh
- 🚀 Multiple users handled simultaneously
- 📋 Structured logging with rotation (console + file)
- 🔄 Session resume — refresh mid-job and it picks back up
- 🚫 Cancel on tab close — server cleans up immediately

---

## 🏗 Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| OCR Engine | Tesseract OCR v4 |
| Image Processing | OpenCV |
| PDF Rendering | pdf2image + poppler |
| PDF Merging | pypdf |
| Parallelism | ProcessPoolExecutor + ThreadPoolExecutor |
| Package Manager | uv |
| Logging | Python logging + RotatingFileHandler |
| Frontend | HTML / CSS / Vanilla JS |

---

## 📂 Project Structure

```
scansutra/
│
├── main.py                  # FastAPI app entry point + stale job cleanup loop
├── requirements.txt
├── pyproject.toml           # uv/pip project config
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── routes.py            # API endpoints
│   ├── job_manager.py       # ProcessPoolExecutor job queue
│   ├── ocr_engine.py        # Tesseract OCR — parallel page processing
│   ├── preprocessing.py     # OpenCV image cleanup
│   ├── pdf_utils.py         # PDF merge + temp file cleanup
│   ├── logger.py            # Centralized logging config
│   └── static/
│       └── index.html       # Frontend UI
│
├── jobs/                    # Auto-created — one isolated folder per upload
│   └── {uuid}/
│       ├── input.pdf        # Deleted after OCR starts
│       ├── temp_page_N.pdf  # Deleted after merge
│       └── output.pdf       # Deleted after download
│
└── logs/
    ├── scansutra.log        # Current log file
    ├── scansutra.log.1      # Rotated (5MB max, 3 kept)
    └── scansutra.log.2
```

---

## ⚙ Installation

### 1. Clone & enter project

```bash
git clone https://github.com/yourusername/scansutra-ocr.git
cd scansutra-ocr
```

### 2. Install `uv`

```bash
# Linux / macOS
curl -Lsf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> `uv` is 10–100x faster than `pip`. It replaces both `pip` and `venv`.

### 3. Create virtual environment + install dependencies

```bash
uv venv --python 3.12
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

uv pip install -r requirements.txt
```

### 4. Install system dependencies

**Ubuntu / Debian:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
brew install tesseract-lang      # Hindi support
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

**One command. No Redis. No Celery. No background services.**

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ocr/` | Upload PDF → returns `job_id` immediately |
| GET | `/api/status/{job_id}` | Poll job progress |
| GET | `/api/result/{job_id}` | Download finished PDF |
| DELETE | `/api/job/{job_id}` | Cancel job (programmatic) |
| POST | `/api/job/{job_id}/cancel` | Cancel job (browser beacon on tab close) |

### Example curl flow

```bash
# 1. Submit
curl -X POST http://localhost:8000/api/ocr/ \
  -F "file=@scan.pdf" \
  -F "lang=eng"
# → {"job_id": "abc-123", "status": "queued"}

# 2. Poll until done
curl http://localhost:8000/api/status/abc-123
# → {"status": "processing", "step": "Starting OCR"}
# → {"status": "done"}

# 3. Download
curl http://localhost:8000/api/result/abc-123 -o output.pdf
```

---

## ⚡ Speed Optimizations

| Optimization | Impact |
|---|---|
| DPI 300 → 200 | ~2x faster PDF-to-image conversion |
| `use_pdftocairo=True` | Faster rendering than default pdftoppm |
| `thread_count` in pdf2image | Parallel page rendering |
| `ThreadPoolExecutor` per job | All pages OCR'd simultaneously |
| `ProcessPoolExecutor` for jobs | Multiple users processed in parallel |
| DPI stamped on preprocessed image | Fixes Tesseract `Invalid resolution 0 dpi` error |
| `COLOR_RGB2GRAY` (not BGR) | Correct grayscale → better OCR accuracy |

### DPI guide

| DPI | Speed | Quality | Use for |
|---|---|---|---|
| 150 | ⚡⚡⚡ Fast | ⭐⭐ OK | Large files, quick preview |
| 200 | ⚡⚡ Good | ⭐⭐⭐ Good | **Default — best balance** |
| 300 | ⚡ Slow | ⭐⭐⭐⭐ High | Legal / archival documents |

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
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_TO_FILE` | `true` | Write logs to `logs/scansutra.log` |
| `LOG_DIR` | `logs` | Directory for log files |

---

## 📋 Logging

Logs go to both console (colored) and file (rotating):

```
2026-03-06 15:41:40 | INFO     | app.routes      | Upload received | filename=scan.pdf | lang=hin
2026-03-06 15:41:40 | INFO     | app.job_manager | Job queued | job_id=abc-123
2026-03-06 15:41:44 | INFO     | app.ocr_engine  | PDF rendered | pages=28 | 3776ms
2026-03-06 15:42:37 | INFO     | app.ocr_engine  | All pages OCR'd | pages=28 | total=48425ms
2026-03-06 15:42:37 | INFO     | app.routes      | Result delivered | job_id=abc-123 | pages=28 | size=2441KB
```

```bash
# Show debug logs (per-page timing)
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Disable file logging
LOG_TO_FILE=false uvicorn main:app --reload
```

Log files rotate at **5MB**, keeping the last **3 files**.

---

## 🔄 Session Handling

| Scenario | Behaviour |
|---|---|
| Normal refresh (F5) | Resumes polling the existing job |
| Tab close / Ctrl+W | `sendBeacon` cancels job on server immediately |
| Hard refresh (Ctrl+Shift+R) | Same as tab close — job cancelled, dir cleaned |
| New upload while job running | Old job cancelled automatically before new one starts |
| Server restart mid-job | Worker detects deleted dir, exits cleanly — no file leaks |

---

## 🛡 Security

- PDF-only file validation (filename extension check)
- 50MB file size limit
- UUID-based isolated job directories
- Automatic cleanup on every path: success, failure, cancel, refresh, shutdown
- No user data retained after download

---

## 📦 uv Cheat Sheet

```bash
# Install uv
curl -Lsf https://astral.sh/uv/install.sh | sh

# Create venv + activate
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Add a new package
uv pip install some-package

# Save current packages
uv pip freeze > requirements.txt

# Check version
uv --version
```

---

## 🔢 Versioning

This project follows [Semantic Versioning](https://semver.org/):

```
vMAJOR.MINOR.PATCH
v2.2.0  — current stable release
```

```bash
# Tag a release
git tag -a v2.2.0 -m "stable release — no Redis required"
git push origin main --tags

# View all versions
git tag

# See changes between versions
git log v2.1.0..v2.2.0 --oneline
```

### Changelog

| Version | Changes |
|---|---|
| v1.0.0 | Initial release — Celery + Redis |
| v2.0.0 | Replaced Celery with ProcessPoolExecutor |
| v2.1.0 | Parallel page processing, speed optimizations |
| v2.1.1 | Fixed BGR→RGB colorspace bug |
| v2.2.0 | Logging, session handling, cancel on refresh, DPI fix |

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