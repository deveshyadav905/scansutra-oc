from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(
    title="ScanSutra OCR",
    description="Convert scanned PDFs into searchable PDFs",
    version="1.0.0"
)

app.include_router(router)

# Serve frontend
app.mount(
    "/",
    StaticFiles(directory="app/static", html=True),
    name="static"
)
