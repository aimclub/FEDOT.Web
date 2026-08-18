"""Import this and the GUI opens by itself.

::

    import fedotweb.autowatch          # noqa: F401

    from fedot import Fedot
    Fedot(problem='classification', timeout=10).fit(features=..., target=...)

The import wraps ``Fedot.fit`` so that every fit starts a watched session: the
server comes up if it is not already running, a browser tab opens on the run, and
the evolution is reported there as it happens.

An explicit ``optimizer=`` argument is left alone -- if you passed your own, this
gets out of the way rather than overriding it.
"""

from __future__ import annotations

import os
from typing import Any

from .attach import watch

#: Set ``FEDOTWEB_AUTOWATCH_BROWSER=0`` on a headless machine; the run is still
#: recorded and the URL still printed.
_OPEN_BROWSER = os.getenv("FEDOTWEB_AUTOWATCH_BROWSER", "1") not in ("0", "false", "False")


def _describe(model: Any) -> dict[str, Any]:
    """A few facts about the run, for the GUI to show beside it."""
    params = getattr(model, "params", None)
    problem = None
    try:
        problem = str(getattr(params, "task", None).task_type.value)
    except Exception:
        problem = None

    described: dict[str, Any] = {"origin": "attached"}
    if problem:
        described["problem"] = problem
    for name in ("timeout", "preset", "pop_size", "num_of_generations"):
        try:
            value = params.get(name)
        except Exception:
            value = None
        if value is not None:
            described[name] = value
    return described


def install() -> None:
    """Wrap ``Fedot.fit``. Calling this twice is harmless."""
    from fedot.api.main import Fedot

    if getattr(Fedot, "_fedotweb_autowatch", False):
        return

    original_init = Fedot.__init__
    original_fit = Fedot.fit

    def __init__(self, *args, **kwargs):
        # Remember whether the caller chose an optimiser, so we know not to
        # replace it. `Fedot` swallows unknown keys into composer params, so the
        # flag has to be captured before the call.
        self._fedotweb_user_optimizer = kwargs.get("optimizer") is not None
        original_init(self, *args, **kwargs)

    def fit(self, *args, **kwargs):
        if getattr(self, "_fedotweb_watching", False):
            return original_fit(self, *args, **kwargs)

        name = kwargs.pop("watch_name", None)
        with watch(name, open_browser=_OPEN_BROWSER, config=_describe(self)) as session:
            self._fedotweb_watching = True
            if not getattr(self, "_fedotweb_user_optimizer", False):
                self.params.update(optimizer=session.optimizer)
            try:
                result = original_fit(self, *args, **kwargs)
            finally:
                self._fedotweb_watching = False
            session.record_result(self)
            return result

    Fedot.__init__ = __init__
    Fedot.fit = fit
    Fedot._fedotweb_autowatch = True


install()
