"""Runtime configuration.

The legacy backend refused to start without a reachable MongoDB.  Here SQLite is
the default so that ``pip install`` followed by ``fedot-web`` is enough to get a
working instance; Mongo can still be switched on for large evolution histories by
setting ``FEDOTWEB_MONGO_URI``.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_workspace() -> Path:
    return Path.home() / ".fedot-web"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FEDOTWEB_", env_file=".env", extra="ignore")

    #: Where uploaded datasets, saved pipelines and run artefacts live.
    workspace: Path = _default_workspace()

    #: Optional MongoDB connection string.  When unset, SQLite is used.
    mongo_uri: str | None = None
    mongo_db: str = "fedot_web"

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False

    #: Origins allowed to call the API.  The Vite dev server runs on 5173.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    #: Hard ceiling on an AutoML run, regardless of what the user asks for.
    max_run_timeout_minutes: float = 240.0

    #: Largest dataset accepted through the upload endpoint.
    max_upload_mb: float = 256.0

    #: How many AutoML runs may execute at the same time.
    max_concurrent_runs: int = 2

    #: Directory holding the built frontend; served at ``/`` when present.
    static_dir: Path | None = None

    @property
    def database_path(self) -> Path:
        return self.workspace / "fedot-web.sqlite"

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
