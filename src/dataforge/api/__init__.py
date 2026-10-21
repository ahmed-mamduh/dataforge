"""FastAPI application factory for DataForge."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dataforge import __version__
from dataforge.api.routes import router

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:3000",
]


def create_app(*, cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(
        title="DataForge API",
        version=__version__,
        description="CSV & Excel data cleaning and transformation API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
