"""Command-line entry point: ``python -m epdeweb`` or ``epde-web``."""

from __future__ import annotations

import argparse

import uvicorn

from .adapters.availability import describe_epde
from .settings import get_settings


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(prog="epde-web", description="Run the EPDE.Web server")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument("--reload", action="store_true", default=settings.reload)
    arguments = parser.parse_args()

    print(f"EPDE.Web workspace: {settings.workspace}")
    availability = describe_epde()
    if availability.available:
        print(f"EPDE {availability.version} detected")
    else:
        # Not fatal: datasets and finished runs are browsable without it, and
        # saying so at startup beats a 503 from the first run the user starts.
        print(f"EPDE is not available: {availability.error}")
    print(f"API docs: http://{arguments.host}:{arguments.port}/docs")

    uvicorn.run(
        "epdeweb.main:app",
        host=arguments.host,
        port=arguments.port,
        reload=arguments.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
