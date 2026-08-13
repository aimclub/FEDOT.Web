"""Shared application state and FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

from ..analysis import AnalysisManager
from ..catalog import OperationCatalog, get_catalog
from ..runs.manager import RunManager
from ..settings import Settings, get_settings
from ..storage.sqlite import Store


class AppState:
    """Objects with a process lifetime, created once during startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = Store(settings.database_path)
        self.manager = RunManager(self.store, settings)
        self.analyses = AnalysisManager(self.store, settings)
        self._catalog: OperationCatalog | None = None

    @property
    def catalog(self) -> OperationCatalog:
        # Building the catalogue imports FEDOT's repositories, which costs a second
        # or two; defer it until something actually asks for operations.
        if self._catalog is None:
            self._catalog = get_catalog()
        return self._catalog


def build_state() -> AppState:
    return AppState(get_settings())


def get_state(request: Request) -> AppState:
    state: AppState | None = getattr(request.app.state, "container", None)
    if state is None:  # pragma: no cover - only reachable if startup failed
        raise HTTPException(status_code=503, detail="Application state is not initialised")
    return state


def get_store(request: Request) -> Store:
    return get_state(request).store


def get_manager(request: Request) -> RunManager:
    return get_state(request).manager


def get_analysis_manager(request: Request) -> AnalysisManager:
    return get_state(request).analyses


def get_operation_catalog(request: Request) -> OperationCatalog:
    return get_state(request).catalog
