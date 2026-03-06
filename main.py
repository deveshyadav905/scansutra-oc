# main.py

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

from app.routes import router
from app.job_manager import shutdown, cleanup_stale_jobs
from app.logger import setup_logging, get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("ScanSutra OCR starting up...")

    # ✅ Stale job cleanup loop — removes abandoned jobs every 30 min
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(1800)
            removed = cleanup_stale_jobs(max_age_seconds=3600)
            if removed:
                log.info(f"Stale job cleanup | removed={removed}")

    task = asyncio.create_task(_cleanup_loop())

    yield

    task.cancel()
    log.info("ScanSutra OCR shutting down...")
    shutdown()


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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    log.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.1f}ms)")
    return response


app.include_router(router, prefix="/api")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)