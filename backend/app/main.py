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

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.auth import verify_admin, verify_token
from app.api.admin import router as admin_router
from app.api.admin_review import router as admin_review_router
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
from app.api.clans import router as clans_router
from app.api.daily_puzzle import router as daily_puzzle_router
from app.api.engagement import router as engagement_router
from app.api.growth import router as growth_router
from app.api.content_editor import router as content_editor_router
from app.api.olympiad import router as olympiad_router
from app.api.olympiad_v2 import router as olympiad_v2_router
from app.api.bookmarks import router as bookmarks_router
from app.api.wavebook import router as wavebook_router
from app.api.questions_v2 import router as questions_v2_router
from app.api.questions_v4 import router as questions_v4_router
from app.api.level import router as level_router
from app.api.user import router as user_router
from app.services.content_store_v2 import bootstrap_v2_from_env, store_v2
from app.services.content_store_v4 import bootstrap_v4_from_env, store_v4
from app.services.content_store_level import bootstrap_level_from_env, level_store
from app.services.pillar_content_store import init_pillar_store
from app.services.firestore_service import is_firestore_available
from app.services.ncert_content_store import init_ncert_store, ncert_store
from app.services.singapore_content_store import init_singapore_store, singapore_store
from app.services.uscc_content_store import init_uscc_store, uscc_store
from app.services.icse_content_store import init_icse_store, icse_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("kiwimath")


def create_app() -> FastAPI:
    is_production = os.environ.get("KIWIMATH_ENV", "").lower() == "production"

    app = FastAPI(
        title="Kiwimath API",
        version="2.0.0",
        description="Adaptive K-5 math olympiad engine with behavioral prediction (PoP model).",
        # In production, disable interactive API docs and the OpenAPI schema.
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    # CORS — restrict to known web origins (Flutter native apps are unaffected
    # by CORS). Override with KIWIMATH_CORS_ORIGINS (comma-separated).
    cors_origins = [
        o.strip()
        for o in os.environ.get(
            "KIWIMATH_CORS_ORIGINS",
            "https://kiwimath-801c1.web.app,https://kiwimath-801c1.firebaseapp.com",
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Auth dependencies:
    #   user_auth  — any signed-in Firebase user (verified ID token)
    #   admin_auth — allowlisted admin (KIWIMATH_ADMIN_EMAILS / KIWIMATH_ADMIN_UIDS)
    user_auth = [Depends(verify_token)]
    admin_auth = [Depends(verify_admin)]

    # Routers — user-facing (require a valid Firebase ID token).
    app.include_router(questions_v2_router, dependencies=user_auth)
    app.include_router(questions_v4_router, dependencies=user_auth)
    app.include_router(level_router, dependencies=user_auth)
    app.include_router(onboarding_router, dependencies=user_auth)
    app.include_router(parent_router, dependencies=user_auth)
    app.include_router(learning_path_router, dependencies=user_auth)
    app.include_router(gamification_router, dependencies=user_auth)
    app.include_router(paywall_router, dependencies=user_auth)
    app.include_router(user_router, dependencies=user_auth)
    app.include_router(companion_router, dependencies=user_auth)
    app.include_router(assessment_router, dependencies=user_auth)
    app.include_router(flag_router, dependencies=user_auth)
    app.include_router(clans_router, dependencies=user_auth)
    app.include_router(daily_puzzle_router, dependencies=user_auth)
    app.include_router(engagement_router, dependencies=user_auth)
    app.include_router(growth_router, dependencies=user_auth)
    app.include_router(olympiad_router, dependencies=user_auth)
    app.include_router(olympiad_v2_router, dependencies=user_auth)
    app.include_router(bookmarks_router, dependencies=user_auth)
    app.include_router(wavebook_router, dependencies=user_auth)

    # Routers — admin-only.
    app.include_router(admin_router, dependencies=admin_auth)
    app.include_router(admin_review_router, dependencies=admin_auth)
    app.include_router(analytics_router, dependencies=admin_auth)
    app.include_router(portal_router, dependencies=admin_auth)
    app.include_router(content_editor_router, dependencies=admin_auth)

    # -----------------------------------------------------------------------
    # Question Editor UI — simple web page for content team
    # -----------------------------------------------------------------------
    @app.get("/editor", response_class=HTMLResponse, dependencies=admin_auth)
    def serve_editor():
        editor_path = Path(__file__).resolve().parent.parent / "static" / "editor.html"
        if editor_path.exists():
            return HTMLResponse(content=editor_path.read_text(), status_code=200)
        return HTMLResponse(content="<h1>Editor not found</h1>", status_code=404)

    @app.get("/admin/dashboard", response_class=HTMLResponse, dependencies=admin_auth)
    def serve_admin_dashboard():
        dash_path = Path(__file__).resolve().parent.parent / "static" / "admin_dashboard.html"
        if dash_path.exists():
            return HTMLResponse(content=dash_path.read_text(), status_code=200)
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

    # -----------------------------------------------------------------------
    # Startup
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # Static files — serve NCERT SVG visuals for Flutter
    # -----------------------------------------------------------------------
    ncert_content_dir = Path(os.environ.get(
        "NCERT_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-live" / "content-v2" / "ncert-curriculum"),
    ))
    if ncert_content_dir.exists():
        app.mount("/static/ncert", StaticFiles(directory=str(ncert_content_dir)), name="ncert_static")
        logger.info(f"Mounted NCERT static files from {ncert_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve Singapore SVG visuals for Flutter
    # -----------------------------------------------------------------------
    singapore_content_dir = Path(os.environ.get(
        "SINGAPORE_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-live" / "content-v2" / "singapore-curriculum"),
    ))
    if singapore_content_dir.exists():
        app.mount("/static/singapore", StaticFiles(directory=str(singapore_content_dir)), name="singapore_static")
        logger.info(f"Mounted Singapore static files from {singapore_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve US Common Core SVG visuals for Flutter
    # -----------------------------------------------------------------------
    uscc_content_dir = Path(os.environ.get(
        "USCC_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-live" / "content-v2" / "us-common-core"),
    ))
    if uscc_content_dir.exists():
        app.mount("/static/uscc", StaticFiles(directory=str(uscc_content_dir)), name="uscc_static")
        logger.info(f"Mounted USCC static files from {uscc_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve ICSE SVG visuals for Flutter
    # -----------------------------------------------------------------------
    icse_content_dir = Path(os.environ.get(
        "ICSE_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-live" / "content-v2" / "icse-curriculum"),
    ))
    if icse_content_dir.exists():
        app.mount("/static/icse", StaticFiles(directory=str(icse_content_dir)), name="icse_static")
        logger.info(f"Mounted ICSE static files from {icse_content_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve Wavebook SVG visuals
    # -----------------------------------------------------------------------
    wavebook_svg_dir = Path(os.environ.get(
        "KIWIMATH_V2_CONTENT_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "content-live" / "content-v2"),
    )) / "wavebook" / "svg"
    if wavebook_svg_dir.exists():
        app.mount("/static/wavebook", StaticFiles(directory=str(wavebook_svg_dir)), name="wavebook_static")
        logger.info(f"Mounted Wavebook SVGs from {wavebook_svg_dir}")

    # -----------------------------------------------------------------------
    # Static files — serve puzzle images for Picture Unravel challenges
    # -----------------------------------------------------------------------
    puzzles_dir = Path(__file__).resolve().parent.parent / "static" / "puzzles"
    if puzzles_dir.exists():
        app.mount("/static/puzzles", StaticFiles(directory=str(puzzles_dir)), name="puzzles_static")
        logger.info(f"Mounted puzzle images from {puzzles_dir}")

    @app.on_event("startup")
    def _startup():
        import time
        t0 = time.time()
        bootstrap_v2_from_env()
        v2_stats = store_v2.stats()
        logger.info(f"V2 content loaded in {time.time()-t0:.1f}s: {v2_stats['total_questions']} questions, {v2_stats['topics']} topics")
        try:
            bootstrap_v4_from_env()
            v4_stats = store_v4.stats()
            logger.info(f"V4 content loaded: {v4_stats['total_questions']} questions, {v4_stats['total_topics']} topics")
        except Exception as e:
            logger.warning(f"V4 store init failed (non-fatal): {e}")
        try:
            bootstrap_level_from_env()
            ls = level_store.stats()
            logger.info(f"Level/Grade content loaded: olympiad={ls['olympiad_total']} curriculum={ls['curriculum_total']}")
        except Exception as e:
            logger.warning(f"Level store init failed (non-fatal): {e}")
        try:
            init_ncert_store()
            logger.info(f"NCERT content: {ncert_store.total_questions} questions loaded")
        except Exception as e:
            logger.warning(f"NCERT store init failed (non-fatal): {e}")
        try:
            init_singapore_store()
            logger.info(f"Singapore content: {singapore_store.total_questions} questions loaded")
        except Exception as e:
            logger.warning(f"Singapore store init failed (non-fatal): {e}")
        try:
            init_uscc_store()
            logger.info(f"USCC content: {uscc_store.total_questions} questions loaded")
        except Exception as e:
            logger.warning(f"USCC store init failed (non-fatal): {e}")
        try:
            init_icse_store()
            logger.info(f"ICSE content: {icse_store.total_questions} questions loaded")
        except Exception as e:
            logger.warning(f"ICSE store init failed (non-fatal): {e}")
        try:
            init_pillar_store()
            from app.services.pillar_content_store import pillar_store
            ps = pillar_store.stats
            logger.info(f"Olympiad v2 pillar content: {ps['total']} questions loaded")
        except Exception as e:
            logger.warning(f"Pillar store init failed (non-fatal): {e}")
        logger.info(f"Firestore: {'connected' if is_firestore_available() else 'unavailable (in-memory mode)'}")
        logger.info(f"Startup complete in {time.time()-t0:.1f}s")

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
        v4_stats = store_v4.stats()
        return {
            "status": "healthy",
            "version": "2.1.0",
            "content_v2": v2_stats,
            "content_v4": v4_stats,
            "content_level": level_store.stats(),
            "firestore": "connected" if is_firestore_available() else "in-memory",
        }

    # Debug endpoint — never registered in production (404 there).
    if not is_production:
        @app.get("/debug/content", dependencies=admin_auth)
        def debug_content():
            """Debug endpoint: shows what content is loaded and filesystem state."""
            content_dir = os.environ.get("KIWIMATH_V2_CONTENT_DIR", "NOT SET")
            dir_exists = os.path.isdir(content_dir) if content_dir != "NOT SET" else False
            dir_contents = []
            if dir_exists:
                try:
                    dir_contents = sorted(os.listdir(content_dir))
                except Exception as e:
                    dir_contents = [f"ERROR: {e}"]
            v2_stats = store_v2.stats()
            # Sample question IDs
            sample_ids = list(store_v2._questions.keys())[:20]
            return {
                "env_var": content_dir,
                "dir_exists": dir_exists,
                "dir_contents": dir_contents,
                "v2_stats": v2_stats,
                "sample_question_ids": sample_ids,
                "memory_mb": _get_memory_mb(),
            }

    def _get_memory_mb():
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            return -1

    # -----------------------------------------------------------------------
    # Content stats (for dashboards / admin)
    # -----------------------------------------------------------------------
    @app.get("/stats", dependencies=user_auth)
    def content_stats():
        """Detailed v2 content statistics."""
        return {
            "version": "2.0.0",
            "content": store_v2.stats(),
        }

    # -----------------------------------------------------------------------
    # Admin CMS UI
    # -----------------------------------------------------------------------
    @app.get("/cms", response_class=HTMLResponse, dependencies=admin_auth)
    def admin_cms():
        admin_path = Path(__file__).parent.parent / "admin.html"
        if admin_path.exists():
            return admin_path.read_text()
        return "<h1>admin.html not found — place it in backend/ folder</h1>"

    # -----------------------------------------------------------------------
    # Test harness (dev only)
    # -----------------------------------------------------------------------
    @app.get("/test", response_class=HTMLResponse, dependencies=admin_auth)
    def test_harness():
        harness_path = Path(__file__).parent.parent / "test_harness.html"
        if harness_path.exists():
            return harness_path.read_text()
        return "<h1>test_harness.html not found</h1>"

    return app


app = create_app()
