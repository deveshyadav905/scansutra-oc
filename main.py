# main.py
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.job_manager import shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    shutdown()  # gracefully terminate worker processes on exit


app = FastAPI(
    title="ScanSutra OCR",
    description="Convert scanned PDFs into searchable PDFs",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API routes MUST come before StaticFiles — StaticFiles catches everything
app.include_router(router, prefix="/api")

app.mount(
    "/",
    StaticFiles(directory="app/static", html=True),
    name="static",
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)