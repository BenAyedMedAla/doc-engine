from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logging_config import configure
from settings import settings

configure()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Doc-engine API starting on %s:%d", settings.api_host, settings.api_port)
    yield
    logger.info("Doc-engine API shutting down")


app = FastAPI(
    title="Doc Engine API",
    description="Multilingual document ingestion and extraction engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import router  # noqa: E402 — imported after app to avoid circular
app.include_router(router, prefix="/api/v1")
