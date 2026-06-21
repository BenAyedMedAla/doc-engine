from __future__ import annotations

import logging

from logging_config import configure
from settings import settings
from storage.manager import JobStore
from worker.celery_app import celery_app

configure()
logger = logging.getLogger(__name__)


def _make_store() -> JobStore:
    return JobStore(settings.redis_url, settings.workspace_root, settings.job_ttl)


def _make_core_config(job_id: str):
    from core.config import Config
    return Config(
        base_dir=settings.workspace_root / job_id,
        vlm_base_url=settings.vlm_base_url,
        vlm_model=settings.vlm_model,
        vlm_max_tokens=settings.vlm_max_tokens,
        vlm_image_dpi=settings.vlm_image_dpi,
        vlm_max_workers=settings.vlm_max_workers,
        vlm_retry_attempts=settings.vlm_retry_attempts,
        vlm_retry_backoff=settings.vlm_retry_backoff,
        vlm_text_threshold=settings.vlm_text_threshold,
        long_pdf_threshold=settings.long_pdf_threshold,
        scanned_long_threshold=settings.scanned_long_threshold,
        scan_char_threshold=settings.scan_char_threshold,
        scan_sample_pages=settings.scan_sample_pages,
        long_head_pages=settings.long_head_pages,
        long_tail_pages=settings.long_tail_pages,
    )


@celery_app.task(bind=True, name="worker.tasks.process_document", max_retries=0)
def process_document(self, job_id: str) -> dict:
    store = _make_store()
    store.update_status(job_id, "processing")
    logger.info("Started processing job %s", job_id)

    try:
        cfg = _make_core_config(job_id)
        from core.pipeline import run
        results = run(cfg, sort_first=True)

        failed = [r for r in results if not r.ok]
        if failed and len(failed) == len(results):
            # All files failed
            errors = "; ".join(str(r.error) for r in failed if r.error)
            store.update_status(job_id, "failed", error=errors)
            logger.error("Job %s failed: %s", job_id, errors)
            return {"job_id": job_id, "status": "failed"}

        store.update_status(job_id, "done")
        logger.info("Job %s done (%d/%d files ok)", job_id, len(results) - len(failed), len(results))
        return {"job_id": job_id, "status": "done"}

    except Exception as exc:
        logger.exception("Job %s raised an unexpected error", job_id)
        store.update_status(job_id, "failed", error=str(exc))
        return {"job_id": job_id, "status": "failed"}
