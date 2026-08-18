"""FastAPI application for FEDOT.Web."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import analysis, catalog, datasets, pipelines, runs
from .api.deps import build_state
from .settings import get_settings

logger = logging.getLogger("fedotweb")

DESCRIPTION = """
Web interface for the [FEDOT](https://github.com/aimclub/FEDOT) AutoML framework
and the [GOLEM](https://github.com/aimclub/GOLEM) optimiser.

* **Catalog** — every operation FEDOT can use, with a typed schema for each hyperparameter.
* **Pipelines** — build, validate, store and export pipelines.
* **Datasets** — upload a CSV and choose a target column.
* **Runs** — launch a composition, follow the evolution live, stop it, inspect the result.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.container = build_state()
    logger.info("Workspace: %s", settings.workspace)

    # A run whose worker this server owned died with the previous process. A run
    # attached from a user's script is different: its events come from that
    # script's own process, which a GUI restart does not interrupt — marking it
    # failed would falsify a run that is still happily going.
    store = app.state.container.store
    for record in store.list_runs():
        if record["status"] in {"pending", "running"}:
            if (record.get("config") or {}).get("origin") == "attached":
                continue
            store.update_run(
                record["uid"],
                status="failed",
                error="The server restarted while this run was in progress",
            )

    # Analyses run in worker processes owned by this server too.
    stale = store.fail_running_analyses("The server restarted while this analysis was in progress")
    if stale:
        logger.info("Marked %d interrupted analyses as failed", stale)

    try:
        yield
    finally:
        await app.state.container.manager.shutdown()
        await app.state.container.analyses.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FEDOT.Web API",
        version="2.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api"
    app.include_router(catalog.router, prefix=api_prefix)
    app.include_router(pipelines.router, prefix=api_prefix)
    app.include_router(datasets.router, prefix=api_prefix)
    app.include_router(runs.router, prefix=api_prefix)
    app.include_router(analysis.router, prefix=api_prefix)

    @app.get("/api/health", tags=["meta"])
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": app.version})

    _mount_frontend(app, settings.static_dir)
    return app


def _mount_frontend(app: FastAPI, static_dir: Path | None) -> None:
    """Serve the built UI from the same origin as the API, when it is present.

    Falls back to a short message so a fresh checkout without a frontend build
    still explains itself rather than returning a bare 404.
    """
    candidates = [static_dir] if static_dir else []
    candidates.append(Path(__file__).resolve().parents[2] / "ui" / "dist")

    build_dir = next((path for path in candidates if path and path.is_dir()), None)
    if build_dir is None:
        @app.get("/", include_in_schema=False)
        def missing_frontend() -> JSONResponse:
            return JSONResponse(
                {
                    "message": "The API is running, but no frontend build was found.",
                    "docs": "/docs",
                    "build_hint": "cd ui && npm install && npm run build",
                }
            )

        return

    assets = build_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = build_dir / "index.html"

    @app.get("/", include_in_schema=False)
    def index_page() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # Client-side routes such as /editor must resolve to the SPA shell, but a
        # request for a real file (favicon, manifest) should still be served.
        # Resolving and checking containment keeps a crafted ../ path from
        # reading files outside the build directory.
        if full_path:
            candidate = (build_dir / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(build_dir.resolve()):
                return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
