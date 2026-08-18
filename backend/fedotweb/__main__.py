"""Command-line entry point: ``python -m fedotweb`` or ``fedot-web``."""

from __future__ import annotations

import argparse

import uvicorn

from .settings import get_settings


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(prog="fedot-web", description="Run the FEDOT.Web server")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--reload", action="store_true", default=settings.reload)
    arguments = parser.parse_args()

    print(f"FEDOT.Web workspace: {settings.workspace}")
    print(f"API docs: http://{arguments.host}:{arguments.port}/docs")

    uvicorn.run(
        "fedotweb.main:app",
        host=arguments.host,
        port=arguments.port,
        reload=arguments.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
