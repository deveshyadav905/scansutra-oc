Here is the updated README with the live demo link added at the top.

```markdown
# 📄 ScanSutra OCR

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit-blue?style=for-the-badge&logo=render)](https://pdf-scransutra.onrender.com)

> Convert scanned PDFs into fully searchable PDFs using **FastAPI + Tesseract OCR + Celery**.

ScanSutra OCR is a modern, high-performance **OCR Web Application**. It transforms non-searchable scanned documents into searchable PDFs using **asynchronous background processing**, ensuring the API remains fast and responsive even for large files.

Supports:
- ✅ English OCR
- ✅ Hindi OCR
- ✅ Multi-language OCR (hin + eng)
- ✅ Asynchronous Background Processing (Celery)
- ✅ PDF preview in browser
- ✅ Download searchable PDF
- ✅ Clean and minimal UI

---

## 🚀 Features

- 📤 Upload scanned PDF
- 🌐 Select OCR language (English / Hindi / Multi)
- 🔍 Convert scanned PDF to searchable PDF
- ⚡ **Non-blocking background processing (Celery + Redis)**
- 👁 Preview processed PDF
- ⬇ Download searchable output
- 🚀 **FastAPI backend API**
- 🧠 OpenCV image preprocessing
- 🛡 Secure file validation
- 🧹 Automatic temporary file cleanup

---

## 🔎 SEO Keywords

OCR Web App, PDF OCR Python, Searchable PDF Generator, FastAPI OCR API, Celery Background Tasks, Async OCR Python, Hindi OCR Tool, English OCR Tool, Multi-language OCR, Tesseract OCR Python, OpenCV PDF Processing, Scanned PDF Converter, OCR SaaS Starter Project, Railway FastAPI Deployment, Python OCR Web Application

---

## 🏗 Tech Stack

- **Framework:** FastAPI
- **Task Queue:** Celery + Redis
- **OCR Engine:** Tesseract OCR
- **Image Processing:** OpenCV
- **PDF Handling:** pdf2image, PyPDF2
- **Math:** NumPy
- **Frontend:** HTML / CSS / JavaScript

---

## 📂 Project Structure

```
ocr_web_app/
│
├── app/
│   ├── main.py              # FastAPI App Entry Point
│   ├── routes.py            # API Endpoints
│   ├── celery.py            # Celery Configuration & App Instance
│   ├── tasks.py             # Background OCR Tasks
│   ├── ocr_engine.py        # Tesseract Logic
│   ├── preprocessing.py     # OpenCV Logic
│   ├── pdf_utils.py         # PDF Manipulation
│   └── static/
│       └── index.html
│
├── uploads/                 # Temporary Upload Directory
├── outputs/                 # Processed PDF Directory
├── requirements.txt
└── README.md
```

---

## ⚙ Installation Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/scansutra-ocr.git
cd scansutra-ocr
```

---

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

OR using uv:

```bash
uv venv
source .venv/bin/activate
```

---

### 3️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

*Ensure `celery` and `redis` are included in your `requirements.txt`.*

---

## 📦 System Dependencies (Required)

### Ubuntu / Debian

```bash
# Tesseract OCR & Languages
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-hin
sudo apt install poppler-utils

# Redis Server (Broker)
sudo apt install redis-server
sudo systemctl start redis-server
```

### macOS

```bash
# Tesseract
brew install tesseract
brew install poppler

# Redis
brew install redis
brew services start redis
```

### Windows

1.  Install Tesseract from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2.  Install Redis for Windows or use Docker:
    ```bash
    docker run -d -p 6379:6379 redis
    ```

---

## ▶ Run Application

Because we use Celery for background tasks, you need to run **three** processes (Redis, Celery Worker, and FastAPI).

### Step 1: Start Redis (Message Broker)
If using Docker:
```bash
docker run -p 6379:6379 redis
```
If installed natively, ensure the service is running.

### Step 2: Start Celery Worker (The "Chef")
Open a new terminal window in the project folder and run:
```bash
celery -A app.celery worker --loglevel=info
```
*(Note: Ensure `app.celery` matches your file structure).*

### Step 3: Start FastAPI Server
Open a third terminal window:
```bash
uvicorn app.main:app --reload
```

Open browser:

```
http://127.0.0.1:8000
```

*Or visit the live demo: https://pdf-scransutra.onrender.com*

---

## 📌 API Endpoint

### Convert PDF (Async)

Submits the PDF to the queue and returns a Task ID.

```
POST /ocr/?lang=eng
POST /ocr/?lang=hin
POST /ocr/?lang=hin+eng
```

*The frontend should poll a status endpoint (e.g., `/tasks/{task_id}`) to check when processing is finished.*

---

## 📈 Use Cases

- Government document digitization
- Hindi voter list OCR
- Legal document scanning
- Archive digitization
- Newspaper scanning
- Multi-language document search
- **High-volume OCR processing**
- OCR SaaS starter template

---

## 🛡 Security

- File type validation (PDF only)
- File size restriction
- UUID-based file naming
- Temporary file cleanup
- Safe file handling
- Async task isolation

---

## 🧠 Future Improvements

- [ ] Docker Compose setup (One-click deployment)
- [ ] Real-time progress updates via WebSockets
- [ ] Multi-file batch upload
- [ ] User authentication & JWT
- [ ] OCR history database storage
- [ ] Cloud storage (S3) integration
- [ ] API key support for SaaS model

---

## 👨‍💻 Author

Devesh Yadav  
Python Backend Developer | OCR & Web Scraping Specialist

---

## 📜 License

MIT License
```