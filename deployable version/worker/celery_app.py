from celery import Celery
from settings import settings

celery_app = Celery(
    "doc_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,   # one task at a time per worker process
    task_acks_late=True,            # ack only after completion — safe on crash
    task_reject_on_worker_lost=True,
    result_expires=settings.job_ttl,
)
