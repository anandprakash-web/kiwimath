"""
Kiwimath FastAPI app entry point (v2-only).

Run locally:
    export KIWIMATH_V2_CONTENT_DIR=~/path/to/content-v2
    uvicorn app.main:app --reload

Docker:
    docker build -t kiwimath-api .
    docker run -p 8000:8000 kiwimath-api

Then visit:
    http://localhost:8000/docs             Swagger UI
    http://localhost:8000/health
"""

import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.assessment import router as assessment_router
from app.api.flag import router as flag_router
from app.api.companion import router as companion_router
from app.api.learning_path import router as learning_path_router
from app.api.onboarding import router as onboarding_router
from app.api.parent import router as parent_router
from app.api.portal import router as portal_router
from app.api.gamification import router as gamification_router
from app.api.paywall import router as paywall_router
from app.api.questions_v2 import router as questions_v2_router
from app.api.user import router as user_router
from app.services.content_store_v2 import bootstrap_v2_from_env, store_v2
from app.services.firestore_service import is_firestore_available
from app.services.ncert_content_store import init_ncert_store, ncert_store
from app.services.singapore_content_store import init_singapore_store, singapore_store
from app.services.uscc_content_store import init_uscc_store, uscc_store
from app.services.icse_content_store import init_icse_store, icse_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("kiwimath")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kiwimath API",
        version="2.0.0",
        description="Adaptive K-5 math olympiad engine with behavioral prediction (PoP model).",
    )

    # CORS — Flutter app + web preview.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Routers — v2 only.
    app.include_router(questions_v2_router)
    app.include_router(onboarding_router)
    app.include_router(parent_router)
    app.include_router(learning_path_router)
    app.include_router(gamification_router)
    app.include_router(paywall_router)
    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(analytics_router)
    app.include_router(companion_router)
    app.include_router(portal_router)
    app.include_router(assessment_router)
    app.include_router(flag_router)

    # -----------------------------------------------------------------------
    # Startup
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # Static files — serve NCERT SVG visuals for Flutter
    # -----------------------------------------------------------------------
    ncert_content_dir = Path(os.environ.get(
        "NCERT_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-v2" / "ncert-curriculum"),
    ))
    if ncert_content_dir.exists():
        app.mount("/static/ncert", StaticFiles(directory=str(ncert_content_dir)), name="ncert_static")
        logger.info(f"Mounted NCERT static files from {ncert_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve Singapore SVG visuals for Flutter
    # -----------------------------------------------------------------------
    singapore_content_dir = Path(os.environ.get(
        "SINGAPORE_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-v2" / "singapore-curriculum"),
    ))
    if singapore_content_dir.exists():
        app.mount("/static/singapore", StaticFiles(directory=str(singapore_content_dir)), name="singapore_static")
        logger.info(f"Mounted Singapore static files from {singapore_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve US Common Core SVG visuals for Flutter
    # -----------------------------------------------------------------------
    uscc_content_dir = Path(os.environ.get(
        "USCC_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-v2" / "us-common-core"),
    ))
    if uscc_content_dir.exists():
        app.mount("/static/uscc", StaticFiles(directory=str(uscc_content_dir)), name="uscc_static")
        logger.info(f"Mounted USCC static files from {uscc_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve ICSE SVG visuals for Flutter
    # -----------------------------------------------------------------------
    icse_content_dir = Path(os.environ.get(
        "ICSE_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-v2" / "icse-curriculum"),
    ))
    if icse_content_dir.exists():
        app.mount("/static/icse", StaticFiles(directory=str(icse_content_dir)), name="icse_static")
        logger.info(f"Mounted ICSE static files from {icse_content_dir}")

    @app.on_event("startup")
    def _startup():
        bootstrap_v2_from_env()
        init_ncert_store()
        logger.info(f"NCERT content: {ncert_store.total_questions} questions loaded")
        init_singapore_store()
        logger.info(f"Singapore content: {singapore_store.total_questions} questions loaded")
        init_uscc_store()
        logger.info(f"USCC content: {uscc_store.total_questions} questions loaded")
        init_icse_store()
        logger.info(f"ICSE content: {icse_store.total_questions} questions loaded")
        logger.info(f"Firestore: {'connected' if is_firestore_available() else 'unavailable (in-memory mode)'}")

    # -----------------------------------------------------------------------
    # Request logging middleware
    # -----------------------------------------------------------------------
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        if not request.url.path.startswith("/health"):
            logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)")
        return response

    # -----------------------------------------------------------------------
    # Health check (Cloud Run uses this)
    # -----------------------------------------------------------------------
    @app.get("/health")
    def health():
        v2_stats = store_v2.stats()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "content": v2_stats,
            "firestore": "connected" if is_firestore_available() else "in-memory",
        }

    # -----------------------------------------------------------------------
    # Content stats (for dashboards / admin)
    # -----------------------------------------------------------------------
    @app.get("/stats")
    def content_stats():
        """Detailed v2 content statistics."""
        return {
            "version": "2.0.0",
            "content": store_v2.stats(),
        }

    # -----------------------------------------------------------------------
    # Admin CMS UI
    # -----------------------------------------------------------------------
    @app.get("/cms", response_class=HTMLResponse)
    def admin_cms():
        admin_path = Path(__file__).parent.parent / "admin.html"
        if admin_path.exists():
            return admin_path.read_text()
        return "<h1>admin.html not found — place it in backend/ folder</h1>"

    # -----------------------------------------------------------------------
    # Test harness (dev only)
    # -----------------------------------------------------------------------
    @app.get("/test", response_class=HTMLResponse)
    def test_harness():
        harness_path = Path(__file__).parent.parent / "test_harness.html"
        if harness_path.exists():
            return harness_path.read_text()
        return "<h1>test_harness.html not found</h1>"

    return app


app = create_app()
