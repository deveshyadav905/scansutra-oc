from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(
    title="ScanSutra OCR",
    description="Convert scanned PDFs into searchable PDFs",
    version="1.0.0"
)

# ✅ API routes MUST be registered before StaticFiles mount
# Otherwise StaticFiles at "/" catches everything first
app.include_router(router, prefix="/api")

# Serve frontend — mounted LAST so API routes take priority
app.mount(
    "/",
    StaticFiles(directory="app/static", html=True),
    name="static"
)