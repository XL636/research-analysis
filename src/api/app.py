"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup / shutdown."""
    # Load API keys from config/.env if present
    env_path = Path("config/.env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    # Startup: ensure upload dir exists
    config = _load_config()
    upload_dir = config.get("api", {}).get("upload_dir", "./uploads")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: nothing to clean up


def _load_config() -> dict:
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = _load_config()
    api_conf = config.get("api", {})

    app = FastAPI(
        title="Research Analysis API",
        description="研讨会/组会分析工具 Web API",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS
    origins = api_conf.get("cors_origins", ["http://localhost:5173"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from src.api.routes.dashboard import router as dashboard_router
    from src.api.routes.knowledge import router as knowledge_router
    from src.api.routes.pipeline import router as pipeline_router
    from src.api.routes.reports import router as reports_router
    from src.api.routes.paper import router as paper_router
    from src.api.routes.settings import router as settings_router

    app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
    app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
    app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
    app.include_router(paper_router, prefix="/api/paper", tags=["Paper"])

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    # Serve static frontend (production build)
    dist_dir = Path(__file__).resolve().parent.parent.parent / "web" / "dist"
    if dist_dir.exists():
        # Serve static assets
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        # SPA fallback: serve index.html for all non-API routes
        from fastapi.responses import FileResponse

        @app.get("/{path:path}", include_in_schema=False)
        async def spa_fallback(path: str):
            # If file exists in dist, serve it; otherwise serve index.html
            file_path = (dist_dir / path).resolve()
            if not file_path.is_relative_to(dist_dir.resolve()):
                return FileResponse(str(dist_dir / "index.html"))
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(dist_dir / "index.html"))

    return app
