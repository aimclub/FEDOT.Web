"""Whether EPDE is installed, and what this build of it can do.

The API is allowed to run without EPDE: a user browsing finished runs, or a
FEDOT.Web instance that merely has the module mounted, should not be made to
install torch. So availability is a fact the server reports rather than an
assumption it makes, and every screen that needs the framework asks first.

The capability flags are probed rather than derived from a version string.
EPDE is developed on master well ahead of its PyPI releases, and the two differ
in ways that matter here -- ``EpdeSearch.__init__`` takes ``dimensionality`` in
1.2.17 and ``use_pic`` / ``device`` on master, and only master carries an
``early_stopping_callback``. Asking the signature is both simpler and more
honest than mapping versions to features.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EpdeAvailability:
    """What the server found when it looked for EPDE."""

    available: bool
    version: str | None = None
    error: str | None = None
    #: Keyword arguments ``EpdeSearch.__init__`` accepts in this build.
    search_kwargs: list[str] = field(default_factory=list)
    #: Keyword arguments ``EpdeSearch.fit`` accepts in this build.
    fit_kwargs: list[str] = field(default_factory=list)
    #: Prepared token families importable from ``epde.interface.prepared_tokens``.
    token_families: list[str] = field(default_factory=list)
    #: Optional extras that change what a run can do.
    features: dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


#: Token families the run configuration screen offers. Each entry is checked
#: against the installed EPDE before it is advertised, so a build without one
#: simply does not show it rather than failing when a run starts.
CANDIDATE_TOKEN_FAMILIES = (
    "TrigonometricTokens",
    "GridTokens",
    "CacheStoredTokens",
    "PhasedSine1DTokens",
    "DataPolynomials",
    "DataSign",
    "ConstantToken",
    "LogfunTokens",
)

_cached: EpdeAvailability | None = None


def describe_epde(refresh: bool = False) -> EpdeAvailability:
    """Probe the installed EPDE. Cached, because importing it is not cheap."""
    global _cached
    if _cached is not None and not refresh:
        return _cached

    if importlib.util.find_spec("epde") is None:
        _cached = EpdeAvailability(
            available=False,
            error=(
                "EPDE is not installed. Install it with "
                "'pip install epde', or from source: "
                "'pip install git+https://github.com/ITMO-NSS-team/EPDE.git'"
            ),
        )
        return _cached

    try:
        epde = importlib.import_module("epde")
        interface = importlib.import_module("epde.interface.interface")
        prepared = importlib.import_module("epde.interface.prepared_tokens")
    except Exception as exc:  # noqa: BLE001 - a broken install must not be fatal
        _cached = EpdeAvailability(available=False, error=f"EPDE could not be imported: {exc}")
        return _cached

    search_cls = getattr(interface, "EpdeSearch", None)
    if search_cls is None:  # pragma: no cover - would mean a very old EPDE
        _cached = EpdeAvailability(
            available=False, error="This EPDE build has no EpdeSearch class"
        )
        return _cached

    search_kwargs = _parameters_of(search_cls.__init__)
    fit_kwargs = _parameters_of(search_cls.fit)

    features = {
        # Multi-objective MOEA/D search; the single-objective path is a
        # different optimiser class with a different population object.
        "multiobjective": True,
        "singleobjective": hasattr(
            importlib.import_module("epde.optimizers.single_criterion.optimizer"),
            "SimpleOptimizer",
        ),
        # Master replaced the complexity axis with a coefficient-stability one
        # behind ``use_pic``; the second Pareto axis means something different
        # depending on it, so the UI needs to know.
        "physics_informed_criterion": "use_pic" in search_kwargs,
        "device_selection": "device" in search_kwargs,
        # A hand-written equation can be turned into a candidate system.
        "equation_translation": _has_attribute(
            "epde.interface.equation_translator", "translate_equation"
        ),
        # Present on master only; used for a graceful mid-run finish.
        "early_stopping_callback": "early_stopping_callback"
        in _parameters_of(
            importlib.import_module("epde.optimizers.moeadd.moeadd").MOEADDOptimizer.optimize
        ),
    }

    _cached = EpdeAvailability(
        available=True,
        version=str(getattr(epde, "__version__", None) or _installed_version()),
        search_kwargs=sorted(search_kwargs),
        fit_kwargs=sorted(fit_kwargs),
        token_families=[name for name in CANDIDATE_TOKEN_FAMILIES if hasattr(prepared, name)],
        features=features,
    )
    return _cached


def _parameters_of(function: Any) -> set[str]:
    try:
        return set(inspect.signature(function).parameters) - {"self"}
    except (TypeError, ValueError):  # pragma: no cover - C-level callables
        return set()


def _has_attribute(module_name: str, attribute: str) -> bool:
    try:
        return hasattr(importlib.import_module(module_name), attribute)
    except Exception:  # noqa: BLE001
        return False


def _installed_version() -> str | None:
    try:
        from importlib.metadata import version

        return version("epde")
    except Exception:  # noqa: BLE001
        return None
