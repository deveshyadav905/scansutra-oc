import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

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

# API Routes first
app.include_router(router, prefix="/api")

# Frontend static files second
app.mount(
    "/",
    StaticFiles(directory="app/static", html=True),
    name="static",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)