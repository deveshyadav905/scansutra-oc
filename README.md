# 📄 ScanSutra OCR

> Convert scanned PDFs into fully searchable PDFs using FastAPI + Tesseract OCR.

ScanSutra OCR is a modern **OCR Web Application** built with **FastAPI**, designed to transform non-searchable scanned documents into searchable PDFs.

Supports:
- ✅ English OCR
- ✅ Hindi OCR
- ✅ Multi-language OCR (hin + eng)
- ✅ PDF preview in browser
- ✅ Download searchable PDF
- ✅ Clean and minimal UI

---

## 🚀 Features

- 📤 Upload scanned PDF
- 🌐 Select OCR language (English / Hindi / Multi)
- 🔍 Convert scanned PDF to searchable PDF
- 👁 Preview processed PDF
- ⬇ Download searchable output
- ⚡ FastAPI backend API
- 🧠 OpenCV image preprocessing
- 🛡 Secure file validation
- 🧹 Automatic temporary file cleanup

---

## 🔎 SEO Keywords

OCR Web App, PDF OCR Python, Searchable PDF Generator, FastAPI OCR API, Hindi OCR Tool, English OCR Tool, Multi-language OCR, Tesseract OCR Python, OpenCV PDF Processing, Scanned PDF Converter, OCR SaaS Starter Project, Railway FastAPI Deployment, Python OCR Web Application

---

## 🏗 Tech Stack

- FastAPI
- Tesseract OCR
- OpenCV
- pdf2image
- PyPDF2
- NumPy
- HTML / CSS / JavaScript

---

## 📂 Project Structure

```
ocr_web_app/
│
├── app/
│   ├── main.py
│   ├── routes.py
│   ├── ocr_engine.py
│   ├── preprocessing.py
│   ├── pdf_utils.py
│   └── static/
│       └── index.html
│
├── uploads/
├── outputs/
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

---

## 📦 System Dependencies (Required)

### Ubuntu / Debian

```bash
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-hin
sudo apt install poppler-utils
```

### macOS

```bash
brew install tesseract
brew install poppler
```

---

## ▶ Run Application

```bash
uvicorn app.main:app --reload
```

Open browser:

```
http://127.0.0.1:8000
```

---

## 📌 API Endpoint

### Convert PDF

```
POST /ocr/?lang=eng
POST /ocr/?lang=hin
POST /ocr/?lang=hin+eng
```

---

## 📈 Use Cases

- Government document digitization
- Hindi voter list OCR
- Legal document scanning
- Archive digitization
- Newspaper scanning
- Multi-language document search
- OCR SaaS starter template

---

## 🛡 Security

- File type validation (PDF only)
- File size restriction
- UUID-based file naming
- Temporary file cleanup
- Safe file handling

---

## 🧠 Future Improvements

- Background task processing
- Progress bar UI
- Multi-file upload
- User authentication
- OCR history storage
- Docker deployment
- Cloud storage (S3) integration
- API key support for SaaS model

---

## 👨‍💻 Author

Devesh Yadav  
Python Backend Developer | OCR & Web Scraping Specialist

---

## 📜 License

MIT License
