"""HTTP surface of the EPDE module.

:func:`build_router` assembles every route under one prefix so the module can be
served on its own or mounted into another application -- FEDOT.Web mounts it at
``/api/epde``. Nothing here imports EPDE: the routes work, and report the
framework as missing, on a machine that never installed it.
"""

from fastapi import APIRouter

from . import catalog, datasets, runs, systems


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(catalog.router)
    router.include_router(datasets.router)
    router.include_router(runs.router)
    router.include_router(systems.router)
    return router


__all__ = ["build_router", "catalog", "datasets", "runs", "systems"]
