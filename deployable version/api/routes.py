from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from schemas import HealthResponse, JobStatus, ResultResponse, UploadResponse
from settings import settings
from storage.manager import JobStore
from worker.tasks import process_document

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = frozenset({
    ".pdf",
    ".docx", ".doc", ".odt", ".rtf",
    ".xlsx", ".xls", ".ods",
    ".pptx", ".ppt", ".odp",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp",
})


def _store() -> JobStore:
    return JobStore(settings.redis_url, settings.workspace_root, settings.job_ttl)


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext!r}")

    content   = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"File too large — max {settings.max_upload_size_mb} MB")

    job_id = str(uuid.uuid4())
    store  = _store()
    store.create_job(job_id, file.filename)
    store.save_upload(job_id, file.filename, content)

    process_document.delay(job_id)
    logger.info("Job %s queued for %s (%d bytes)", job_id, file.filename, len(content))

    return UploadResponse(job_id=job_id, filename=file.filename)


# ── Status ─────────────────────────────────────────────────────────────────────

@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    job = _store().get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id!r} not found")
    return JobStatus(**job)


# ── Result ─────────────────────────────────────────────────────────────────────

@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str):
    store = _store()
    job   = store.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id!r} not found")
    if job["status"] != "done":
        raise HTTPException(409, f"Job not done yet — current status: {job['status']!r}")

    result = store.get_result(job_id)
    if not result:
        raise HTTPException(500, "Job is marked done but output files are missing")

    markdown, summary = result
    return ResultResponse(
        job_id=job_id,
        status=job["status"],
        filename=job["filename"],
        markdown=markdown,
        summary=summary,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────

@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    store = _store()
    if not store.get_job(job_id):
        raise HTTPException(404, f"Job {job_id!r} not found")
    store.delete_job(job_id)
    return JSONResponse(status_code=204, content=None)


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health():
    redis_ok = _store().ping()
    return HealthResponse(
        status="ok" if redis_ok else "degraded",
        redis="ok" if redis_ok else "error",
    )
