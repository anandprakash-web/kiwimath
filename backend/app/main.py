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
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.companion import router as companion_router
from app.api.portal import router as portal_router
from app.api.gamification import router as gamification_router
from app.api.questions_v2 import router as questions_v2_router
from app.api.user import router as user_router
from app.services.content_store_v2 import bootstrap_v2_from_env, store_v2
from app.services.firestore_service import is_firestore_available

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
    app.include_router(gamification_router)
    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(analytics_router)
    app.include_router(companion_router)
    app.include_router(portal_router)

    # -----------------------------------------------------------------------
    # Startup
    # -----------------------------------------------------------------------
    @app.on_event("startup")
    def _startup():
        bootstrap_v2_from_env()
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
