#!/usr/bin/env python3
"""
Backend API — submit a batch of files in one request, poll status, fetch results.

Single FastAPI process, no Celery/Redis: each batch is processed in a
background thread (Starlette's threadpool) calling pipeline.run() directly.
The existing per-parser semaphores in pipeline.py (_OFFICE_SLOTS/_DOCLING_SLOTS/
_VLM_SLOTS) are module-level, so concurrent batches still share the same
GPU/CPU concurrency limits.

Run:
  /home/nullkuhl/docling-kreuzberg-benchmark-1/myenv/bin/python3 -m uvicorn api:app \
      --host 0.0.0.0 --port 8080 --workers 1

Endpoints:
  POST   /api/v1/batches            multipart upload, one or more files → batch_id
  GET    /api/v1/batches/{id}       status + per-file progress
  GET    /api/v1/batches/{id}/result  per-file markdown once status == "done"
  DELETE /api/v1/batches/{id}       remove job state + files on disk
  GET    /api/v1/health             liveness check

Config overrides (env vars, read at startup):
  DOC_ENGINE_WORKSPACE   workspace root for batch input/output (default: ./workspace)
  DOC_ENGINE_VLM_URL     OpenAI-compatible VLM endpoint base URL
  DOC_ENGINE_VLM_MODEL   VLM model name

NOTE: --workers must stay at 1 — in-memory batch state (_batches) is not
shared across processes. Scale by running multiple batches concurrently
within this one process, not by adding uvicorn workers.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import Config
from pipeline import run

# ── Workspace ──────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(os.environ.get("DOC_ENGINE_WORKSPACE", Path(__file__).parent / "workspace")).resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

_VLM_URL   = os.environ.get("DOC_ENGINE_VLM_URL")
_VLM_MODEL = os.environ.get("DOC_ENGINE_VLM_MODEL")

Status = Literal["queued", "processing", "done", "failed"]
FileStatusValue = Literal["pending", "ok", "error"]


# ── In-memory job state ────────────────────────────────────────────────────────

@dataclass
class FileState:
    filename: str
    status: FileStatusValue = "pending"
    parser: str | None = None
    pages: int | None = None
    table_count: int | None = None
    elapsed_s: float | None = None
    error: str | None = None
    markdown: str | None = None


@dataclass
class Batch:
    batch_id: str
    filenames: list[str]
    status: Status = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error: str | None = None
    files: dict[str, FileState] = field(default_factory=dict)


_batches: dict[str, Batch] = {}
_lock = threading.Lock()


def _batch_dir(batch_id: str) -> Path:
    return WORKSPACE_ROOT / batch_id


def _unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suf = dest.stem, dest.suffix
    i = 1
    while True:
        candidate = dest.with_name(f"{stem}_{i}{suf}")
        if not candidate.exists():
            return candidate
        i += 1


# ── Background processing ─────────────────────────────────────────────────────

def _process_batch(batch_id: str, cfg: Config, input_paths: list[Path]) -> None:
    with _lock:
        batch = _batches[batch_id]
        batch.status = "processing"
        batch.updated_at = time.time()

    try:
        results = run(cfg, sort_first=False, input_paths=input_paths)
    except Exception as exc:
        with _lock:
            batch.status = "failed"
            batch.error = str(exc)
            batch.updated_at = time.time()
        return

    with _lock:
        for r in results:
            state = batch.files.get(r.source.name)
            if state is None:
                continue
            if r.ok:
                md_path = cfg.output_dir / (r.source.stem + ".md")
                state.status = "ok"
                state.parser = r.parser
                state.pages = r.page_count
                state.table_count = r.extras.get("table_count")
                state.elapsed_s = r.extras.get("elapsed_s")
                state.markdown = md_path.read_text(encoding="utf-8") if md_path.exists() else None
            else:
                state.status = "error"
                state.parser = r.parser
                state.error = r.error
                state.elapsed_s = r.extras.get("elapsed_s")
        batch.status = "done"
        batch.updated_at = time.time()


# ── API models ─────────────────────────────────────────────────────────────────

class BatchAccepted(BaseModel):
    batch_id: str
    status: Status
    files: list[str]


class FileStatusOut(BaseModel):
    filename: str
    status: FileStatusValue
    parser: str | None = None
    pages: int | None = None
    table_count: int | None = None
    elapsed_s: float | None = None
    error: str | None = None


class BatchStatusOut(BaseModel):
    batch_id: str
    status: Status
    created_at: float
    updated_at: float
    error: str | None
    files: list[FileStatusOut]


class FileResultOut(BaseModel):
    filename: str
    status: FileStatusValue
    parser: str | None = None
    pages: int | None = None
    table_count: int | None = None
    error: str | None = None
    markdown: str | None = None


class BatchResultOut(BaseModel):
    batch_id: str
    status: Status
    files: list[FileResultOut]


class HealthOut(BaseModel):
    status: Literal["ok"]


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Document Ingestion Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/batches", response_model=BatchAccepted, status_code=202)
async def create_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(400, "No files provided")

    batch_id = uuid.uuid4().hex
    input_dir = _batch_dir(batch_id) / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    file_states: dict[str, FileState] = {}
    for f in files:
        safe_name = Path(f.filename or "upload").name  # strip any path components
        dest = _unique_dest(input_dir / safe_name)
        content = await f.read()
        dest.write_bytes(content)
        saved_paths.append(dest)
        file_states[dest.name] = FileState(filename=dest.name)

    cfg = Config(base_dir=_batch_dir(batch_id))
    if _VLM_URL:
        cfg.vlm_base_url = _VLM_URL
    if _VLM_MODEL:
        cfg.vlm_model = _VLM_MODEL

    batch = Batch(batch_id=batch_id, filenames=list(file_states), files=file_states)
    with _lock:
        _batches[batch_id] = batch

    background_tasks.add_task(_process_batch, batch_id, cfg, saved_paths)

    return BatchAccepted(batch_id=batch_id, status="queued", files=list(file_states))


@app.get("/api/v1/batches/{batch_id}", response_model=BatchStatusOut)
def get_batch_status(batch_id: str):
    with _lock:
        batch = _batches.get(batch_id)
        if batch is None:
            raise HTTPException(404, "Unknown batch_id")
        return BatchStatusOut(
            batch_id=batch.batch_id,
            status=batch.status,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            error=batch.error,
            files=[
                FileStatusOut(
                    filename=s.filename, status=s.status, parser=s.parser,
                    pages=s.pages, table_count=s.table_count,
                    elapsed_s=s.elapsed_s, error=s.error,
                )
                for s in batch.files.values()
            ],
        )


@app.get("/api/v1/batches/{batch_id}/result", response_model=BatchResultOut)
def get_batch_result(batch_id: str):
    with _lock:
        batch = _batches.get(batch_id)
        if batch is None:
            raise HTTPException(404, "Unknown batch_id")
        if batch.status in ("queued", "processing"):
            raise HTTPException(409, f"Batch not finished yet (status={batch.status})")
        return BatchResultOut(
            batch_id=batch.batch_id,
            status=batch.status,
            files=[
                FileResultOut(
                    filename=s.filename, status=s.status, parser=s.parser,
                    pages=s.pages, table_count=s.table_count,
                    error=s.error, markdown=s.markdown,
                )
                for s in batch.files.values()
            ],
        )


@app.delete("/api/v1/batches/{batch_id}", status_code=204)
def delete_batch(batch_id: str):
    with _lock:
        batch = _batches.get(batch_id)
        if batch is None:
            raise HTTPException(404, "Unknown batch_id")
        if batch.status == "processing":
            raise HTTPException(409, "Cannot delete a batch that is still processing")
        del _batches[batch_id]

    import shutil
    shutil.rmtree(_batch_dir(batch_id), ignore_errors=True)


@app.get("/api/v1/health", response_model=HealthOut)
def health():
    return HealthOut(status="ok")
