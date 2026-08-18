"""FEDOT.Web — a web interface for the FEDOT AutoML framework and GOLEM.

To watch a run you start yourself, see :func:`fedotweb.watch`, or simply
``import fedotweb.autowatch`` and the GUI opens on the next ``fit``.
"""

__version__ = "2.1.0"


def __getattr__(name: str):
    # Imported lazily so that `import fedotweb` stays cheap for the server, which
    # does not need the attach machinery.
    if name in ("watch", "ensure_server", "WatchSession"):
        from . import attach

        return getattr(attach, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["WatchSession", "ensure_server", "watch"]
