"""
Kiwimath FastAPI app entry point.

Run locally:
    export KIWIMATH_CONTENT_DIR=~/Documents/Kiwimath-Content/Grade1
    uvicorn app.main:app --reload

Then visit:
    http://localhost:8000/docs             Swagger UI
    http://localhost:8000/health
    http://localhost:8000/questions/next?locale=IN
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.preview import router as preview_router
from app.api.questions import router as questions_router
from app.services import content_store


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kiwimath API",
        version="0.1.0",
        description="Adaptive Grade-1 math engine. v0 Android backend.",
    )

    # During dev the Flutter app hits us from anywhere. Tighten in prod.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(questions_router)
    app.include_router(preview_router)

    @app.on_event("startup")
    def _startup():
        content_store.bootstrap_from_env()

    return app


app = create_app()
