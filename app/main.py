from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingestion, master_price
from app.core.database import init_db

app = FastAPI(title="Medical Bill Validator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Ensure directory exists
os.makedirs("raw_storage", exist_ok=True)
app.mount("/raw_storage", StaticFiles(directory="raw_storage"), name="raw_storage")


@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(master_price.router, prefix="/api/v1", tags=["Master Price"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
