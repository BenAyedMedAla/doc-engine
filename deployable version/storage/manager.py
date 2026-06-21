from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import redis as redis_lib


class JobStore:
    """
    Manages job lifecycle:
      - State (status, timestamps, error) stored in Redis with TTL
      - Uploaded files and result files stored on disk under workspace_root/{job_id}/
    """

    def __init__(self, redis_url: str, workspace_root: Path, job_ttl: int = 86400):
        self._r         = redis_lib.from_url(redis_url, decode_responses=True)
        self._workspace = workspace_root
        self._ttl       = job_ttl

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _key(self, job_id: str) -> str:
        return f"job:{job_id}"

    def job_workspace(self, job_id: str) -> Path:
        return self._workspace / job_id

    # ── Job state ──────────────────────────────────────────────────────────────

    def create_job(self, job_id: str, filename: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._r.setex(
            self._key(job_id),
            self._ttl,
            json.dumps({
                "job_id":     job_id,
                "status":     "queued",
                "filename":   filename,
                "created_at": now,
                "updated_at": now,
                "error":      None,
            }),
        )

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        raw = self._r.get(self._key(job_id))
        if not raw:
            return
        data = json.loads(raw)
        data["status"]     = status
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if error is not None:
            data["error"] = error
        self._r.setex(self._key(job_id), self._ttl, json.dumps(data))

    def get_job(self, job_id: str) -> dict | None:
        raw = self._r.get(self._key(job_id))
        return json.loads(raw) if raw else None

    # ── File I/O ───────────────────────────────────────────────────────────────

    def save_upload(self, job_id: str, filename: str, content: bytes) -> Path:
        dest = self.job_workspace(job_id) / "input" / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return dest

    def get_result(self, job_id: str) -> tuple[str, dict] | None:
        """Return (combined_markdown, summary_dict) or None if output not ready."""
        output_dir  = self.job_workspace(job_id) / "output"
        md_files    = sorted(f for f in output_dir.glob("*.md") if not f.name.startswith("_"))
        summary_file = output_dir / "_summary.json"

        if not md_files or not summary_file.exists():
            return None

        markdown = "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in md_files)
        summary  = json.loads(summary_file.read_text(encoding="utf-8"))
        return markdown, summary

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def delete_job(self, job_id: str) -> None:
        self._r.delete(self._key(job_id))
        ws = self.job_workspace(job_id)
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)

    # ── Health ─────────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        try:
            return bool(self._r.ping())
        except Exception:
            return False
