"""Runtime configuration.

Mirrors the layout of the FEDOT.Web backend — SQLite by default, a workspace
directory holding datasets and run artefacts — but keeps its own prefix and its
own workspace so the two can run side by side, or one without the other.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_workspace() -> Path:
    return Path.home() / ".epde-web"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EPDEWEB_", env_file=".env", extra="ignore")

    #: Where uploaded fields, discovered systems and run artefacts live.
    workspace: Path = _default_workspace()

    host: str = "127.0.0.1"
    port: int = 8010
    reload: bool = False

    #: Origins allowed to call the API. The Vite dev server runs on 5173.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    #: Hard ceiling on a discovery run, regardless of what the user asks for.
    max_run_timeout_minutes: float = 240.0

    #: Largest accepted field upload. Field data is dense, so this is generous.
    max_upload_mb: float = 512.0

    #: How many discovery runs may execute at the same time.
    max_concurrent_runs: int = 2

    #: Ceiling on the number of grid nodes a single variable may have. Derivative
    #: preprocessing is O(nodes) with a large constant, and a careless upload of a
    #: 4D field is otherwise indistinguishable from a hang.
    max_grid_nodes: int = 4_000_000

    #: Directory holding a built frontend; served at ``/`` when running standalone.
    static_dir: Path | None = None

    @property
    def database_path(self) -> Path:
        return self.workspace / "epde-web.sqlite"

    @property
    def datasets_dir(self) -> Path:
        return self.workspace / "datasets"

    @property
    def runs_dir(self) -> Path:
        return self.workspace / "runs"

    def ensure_directories(self) -> None:
        for directory in (self.workspace, self.datasets_dir, self.runs_dir):
            directory.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings
