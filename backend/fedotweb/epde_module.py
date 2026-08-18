"""Optional mounting of the EPDE mode.

The equation-discovery mode lives in its own package (``epde-backend/epdeweb``)
with its own dependencies, its own workspace and its own database. FEDOT.Web
does not depend on it: this module is the entire coupling, and it is one
``try: import``.

That is deliberate. EPDE does not use GOLEM and brings torch and scikit-learn
with it; an installation that only wants AutoML should not carry them, and the
EPDE side should stay separable enough to become EPDE.Web on its own later
without a migration. So the module is mounted when it happens to be importable
and is simply absent otherwise -- ``GET /api/capabilities`` reports which, and
the frontend hides the whole mode when it is not there rather than offering
screens whose every request would 404.

Note the two-stage check. The package being importable is not the same as EPDE
being installed: ``epdeweb`` runs fine without it and reports the framework as
missing through its own ``/api/epde/capabilities``, which is what lets a user
browse finished runs, or read the configuration screens, before installing
anything.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger("fedotweb.epde")

#: Where the EPDE routes are served from, when they are served at all.
API_PREFIX = "/api/epde"

_mounted = False
_state = None


def is_mounted() -> bool:
    return _mounted


async def shutdown() -> None:
    """Stop any EPDE worker the mounted module owns.

    Called from FEDOT.Web's lifespan rather than from a shutdown event: a host
    that supplies its own ``lifespan`` makes Starlette ignore ``on_event``
    handlers, so a module that registered one would leave its worker processes
    running after the server exits.
    """
    if _state is None:
        return
    await _state.manager.shutdown()


def mount(app: FastAPI, *, prefix: str = API_PREFIX) -> bool:
    """Add the EPDE routes to ``app`` if the module is installed.

    Returns whether it was mounted. Failure is never fatal: the AutoML side of
    the application must start on a machine where the EPDE module is missing or
    broken, which is the normal case.
    """
    global _mounted, _state
    try:
        from epdeweb.main import attach_to
    except ImportError:
        logger.info(
            "The EPDE module is not installed; the equation-discovery mode is off. "
            "Install it with 'pip install -e epde-backend'."
        )
        return False

    try:
        _state = attach_to(app, prefix=prefix)
    except Exception as exc:  # noqa: BLE001 - a broken module must not stop the server
        logger.warning("The EPDE module failed to mount: %s", exc, exc_info=True)
        return False

    _mounted = True
    logger.info("EPDE module mounted at %s", prefix)
    return True
