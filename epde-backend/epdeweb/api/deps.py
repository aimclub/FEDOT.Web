"""Shared application state and FastAPI dependencies.

The state object is deliberately importable and constructible on its own: when
the module is mounted inside FEDOT.Web there is already an application state,
and this one has to live beside it rather than replace it.
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from ..datasets.service import DatasetService
from ..runs.manager import RunManager
from ..settings import Settings, get_settings
from ..storage.sqlite import Store

#: Attribute the state is stashed under on ``app.state``. Namespaced so that
#: mounting into FEDOT.Web cannot collide with its own ``container``.
STATE_ATTRIBUTE = "epde_container"


class AppState:
    """Objects with a process lifetime, created once during startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = Store(settings.database_path)
        self.manager = RunManager(self.store, settings)
        self.datasets = DatasetService(self.store, settings)


def build_state(settings: Settings | None = None) -> AppState:
    return AppState(settings or get_settings())


def get_state(request: Request) -> AppState:
    state: AppState | None = getattr(request.app.state, STATE_ATTRIBUTE, None)
    if state is None:  # pragma: no cover - only reachable if startup failed
        raise HTTPException(status_code=503, detail="The EPDE module is not initialised")
    return state


def get_store(request: Request) -> Store:
    return get_state(request).store


def get_manager(request: Request) -> RunManager:
    return get_state(request).manager


def get_datasets(request: Request) -> DatasetService:
    return get_state(request).datasets


def get_run_settings(request: Request) -> Settings:
    return get_state(request).settings
