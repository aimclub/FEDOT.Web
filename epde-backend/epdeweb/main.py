"""The EPDE.Web application, standalone or mounted.

Two entry points, deliberately:

:func:`create_app`
    a complete FastAPI application, which is what ``python -m epdeweb`` serves.
:func:`attach_to`
    the same routes grafted onto somebody else's application, which is how
    FEDOT.Web offers the EPDE mode without taking on EPDE as a dependency.

Both share one startup routine, so a run left behind by a killed server is
reconciled the same way whichever way the module is being served.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import build_router
from .api.deps import STATE_ATTRIBUTE, AppState, build_state
from .settings import Settings, get_settings

logger = logging.getLogger("epdeweb")

#: Where FEDOT.Web mounts this module, and therefore the path the bundled
#: frontend is built against.
MOUNT_PREFIX = "/api/epde"

DESCRIPTION = """
Web interface for [EPDE](https://github.com/ITMO-NSS-team/EPDE), which discovers
differential equations from data by evolutionary search.

* **Datasets** - upload a field and its grid, or start from a built-in example
  whose governing equation is known.
* **Runs** - configure a search, watch the Pareto front move generation by
  generation, and steer the operators while it runs.
* **Lineage** - the genealogy of the search: which candidate was crossed or
  mutated into which, and which of those lines reached the final front.
* **Systems** - the discovered equations, with the per-term ablation that shows
  what each one actually rests on.
"""


def reconcile_interrupted_runs(state: AppState) -> int:
    """Fail runs whose worker died with a previous server process.

    Every EPDE run is driven by a worker this server owns, so anything still
    marked running after a restart is definitionally dead -- and would otherwise
    be polled by the GUI forever.
    """
    stale = 0
    for record in state.store.list_runs():
        if record["status"] in {"pending", "running"}:
            state.store.update_run(
                record["uid"],
                status="failed",
                error="The server restarted while this run was in progress",
            )
            stale += 1
    return stale


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    state = build_state(settings)
    setattr(app.state, STATE_ATTRIBUTE, state)
    logger.info("EPDE.Web workspace: %s", settings.workspace)

    stale = reconcile_interrupted_runs(state)
    if stale:
        logger.info("Marked %d interrupted EPDE run(s) as failed", stale)

    try:
        yield
    finally:
        await state.manager.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="EPDE.Web API",
        version=__version__,
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

    app.include_router(build_router(), prefix="/api")
    # The bundled frontend is built once and served by whichever process is
    # running, so it has to find the API at the same path in both. Mounting the
    # same routes a second time under the path FEDOT.Web uses costs nothing and
    # saves a separate build for the standalone case; it is hidden from the
    # schema so the reference documents each endpoint once.
    app.include_router(build_router(), prefix=MOUNT_PREFIX, include_in_schema=False)

    @app.get("/api/health", tags=["meta"])
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "version": app.version})

    _mount_frontend(app, settings.static_dir)
    return app


def attach_to(app: FastAPI, *, prefix: str = MOUNT_PREFIX, settings: Settings | None = None) -> AppState:
    """Serve the EPDE module from an existing application.

    Used by FEDOT.Web, which calls this only when the module is importable. The
    state lives under its own attribute and the module keeps its own workspace
    and database, so mounting adds routes and nothing else -- neither
    application can corrupt the other's data, and the EPDE side can later be
    split out without a migration.
    """
    state = build_state(settings or get_settings())
    setattr(app.state, STATE_ATTRIBUTE, state)
    app.include_router(build_router(), prefix=prefix)

    stale = reconcile_interrupted_runs(state)
    if stale:
        logger.info("Marked %d interrupted EPDE run(s) as failed", stale)

    # No ``on_event('shutdown')`` here on purpose: a host that supplies its own
    # ``lifespan`` -- which FEDOT.Web does -- makes Starlette ignore the event
    # handlers entirely, so a worker process would outlive the server. The
    # caller owns the returned state and is expected to shut it down.
    return state


def _mount_frontend(app: FastAPI, static_dir: Path | None) -> None:
    """Serve a built UI from the same origin as the API, when one is present."""
    candidates = [static_dir] if static_dir else []
    candidates.append(Path(__file__).resolve().parents[2] / "ui" / "dist")

    build_dir = next((path for path in candidates if path and path.is_dir()), None)
    if build_dir is None:
        @app.get("/", include_in_schema=False)
        def missing_frontend() -> JSONResponse:
            return JSONResponse(
                {
                    "message": "The EPDE.Web API is running, but no frontend build was found.",
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
    def index_page() -> RedirectResponse:
        # The bundled build is FEDOT.Web's frontend, whose landing page is the
        # AutoML side. Served on its own, this process has no AutoML API behind
        # it, so land on the equation screens instead of on a page whose every
        # request would fail.
        return RedirectResponse(url="/epde/runs")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # Client-side routes must resolve to the SPA shell, but a request for a
        # real file should still be served. Resolving and checking containment
        # keeps a crafted ../ path from reading outside the build directory.
        if full_path:
            candidate = (build_dir / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(build_dir.resolve()):
                return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
