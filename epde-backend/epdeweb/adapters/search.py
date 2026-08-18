"""Building an ``EpdeSearch`` from a run configuration.

EPDE is developed on master well ahead of its releases, and the constructor is
where the two diverge most: 1.2.17 takes ``dimensionality``, master dropped it
and added ``use_pic``, ``device`` and a solver backend. A GUI that hard-coded
either would break against the other, and the failure would surface as a
``TypeError`` several seconds into a run rather than at configuration time.

So every call into EPDE here is filtered through the signature of the installed
build: arguments it does not accept are dropped and reported, rather than
passed and raised on. The same filtering covers ``fit`` and the prepared token
families.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

#: Preprocessors EPDE ships, in the order they appear in the configuration UI.
PREPROCESSORS = ("poly", "ANN", "spectral")

#: Token families the GUI can add to the pool, described independently of EPDE
#: so the catalogue endpoint works without it installed.
TOKEN_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "id": "trigonometric",
        "class": "TrigonometricTokens",
        "label": "Trigonometric",
        "description": "sin and cos of the coordinates, with an evolvable frequency.",
        "params": [
            {"name": "freq_min", "type": "number", "default": 1.5708, "label": "Lowest frequency"},
            {"name": "freq_max", "type": "number", "default": 6.2832, "label": "Highest frequency"},
            {
                "name": "meaningful",
                "type": "boolean",
                "default": False,
                "label": "May stand alone in a term",
            },
        ],
    },
    {
        "id": "grid",
        "class": "GridTokens",
        "label": "Coordinates",
        "description": "The coordinates themselves, so terms like 't * du/dt' can be formed.",
        "params": [
            {"name": "max_power", "type": "integer", "default": 1, "label": "Highest power"},
        ],
    },
    {
        "id": "polynomial",
        "class": "DataPolynomials",
        "label": "Powers of the variable",
        "description": "Powers of the modelled field, for nonlinear terms such as u^2.",
        "params": [
            {"name": "max_power", "type": "integer", "default": 2, "label": "Highest power"},
        ],
    },
    {
        "id": "sign",
        "class": "DataSign",
        "label": "Sign of the variable",
        "description": "sign(u), for models with switching behaviour.",
        "params": [
            {"name": "max_power", "type": "integer", "default": 1, "label": "Highest power"},
        ],
    },
    {
        "id": "phased_sine",
        "class": "PhasedSine1DTokens",
        "label": "Phased sine (1D)",
        "description": "A sine with an evolvable phase; one-dimensional problems only.",
        "params": [
            {"name": "freq_min", "type": "number", "default": 1.5708, "label": "Lowest frequency"},
            {"name": "freq_max", "type": "number", "default": 6.2832, "label": "Highest frequency"},
        ],
    },
)

TOKEN_FAMILY_BY_ID = {family["id"]: family for family in TOKEN_FAMILIES}


@dataclass
class BuildReport:
    """What was asked for versus what this EPDE build accepted."""

    dropped_search_kwargs: list[str] = field(default_factory=list)
    dropped_fit_kwargs: list[str] = field(default_factory=list)
    skipped_token_families: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    #: What the constructed search settled on for ``use_pic``, read back from
    #: the object rather than from the request: the run may not have asked, and
    #: the build's own default decides what the second Pareto axis measures.
    use_pic: bool | None = None

    def messages(self) -> list[str]:
        messages = list(self.notes)
        if self.dropped_search_kwargs:
            messages.append(
                "This EPDE build does not accept "
                + ", ".join(sorted(self.dropped_search_kwargs))
                + " when constructing the search; the defaults were used instead."
            )
        if self.dropped_fit_kwargs:
            messages.append(
                "This EPDE build does not accept "
                + ", ".join(sorted(self.dropped_fit_kwargs))
                + " in fit(); those settings had no effect."
            )
        for family in self.skipped_token_families:
            messages.append(f"Token family '{family}' is not available in this EPDE build.")
        return messages


def supported(function: Any) -> set[str]:
    try:
        return set(inspect.signature(function).parameters) - {"self"}
    except (TypeError, ValueError):  # pragma: no cover - C-level callables
        return set()


def filter_kwargs(function: Any, candidate: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Split a keyword mapping into what ``function`` takes and what it does not."""
    accepted = supported(function)
    if not accepted:
        return dict(candidate), []
    kept = {key: value for key, value in candidate.items() if key in accepted}
    dropped = [key for key in candidate if key not in accepted]
    return kept, dropped


# ------------------------------------------------------------------- the search


def build_search(config: dict[str, Any], grids: list[Any], report: BuildReport) -> Any:
    """Construct and configure the ``EpdeSearch`` a run needs."""
    from epde.interface.interface import EpdeSearch

    dimensionality = max(len(grids) - 1, 0)
    verbose = {
        "show_iter_idx": False,
        "show_warnings": False,
        # EPDE prints every candidate it evaluates at default verbosity, which
        # for a real run is tens of thousands of lines into the worker log.
        "show_iter_fitness": False,
        "show_iter_stats": False,
    }

    candidate: dict[str, Any] = {
        "multiobjective_mode": bool(config.get("multiobjective", True)),
        "use_default_strategy": True,
        "boundary": config.get("boundary", 0),
        "coordinate_tensors": grids,
        "verbose_params": verbose,
        "memory_for_cache": config.get("memory_for_cache", 15),
        "use_solver": False,
        "dimensionality": dimensionality,
        "device": config.get("device", "cpu"),
        "time_axis": int(config.get("time_axis", 0)),
    }
    if config.get("use_pic") is not None:
        candidate["use_pic"] = bool(config["use_pic"])

    kwargs, dropped = filter_kwargs(EpdeSearch.__init__, candidate)
    report.dropped_search_kwargs.extend(dropped)
    # ``verbose_params`` is filtered to what this build's VerboseManager knows;
    # an unknown key there is a TypeError deep inside EPDE's own init.
    kwargs["verbose_params"] = _filter_verbose(verbose)

    search = EpdeSearch(**kwargs)
    # Read the flag back rather than trusting the request: when the run did not
    # ask, the build's own default decides, and on master that default is True.
    report.use_pic = getattr(search, "_use_pic", None)

    preprocessor = str(config.get("preprocessor") or "poly")
    if preprocessor not in PREPROCESSORS:
        preprocessor = "poly"
        report.notes.append("Unknown preprocessor requested; the polynomial one was used.")
    search.set_preprocessor(
        default_preprocessor_type=preprocessor,
        preprocessor_kwargs=dict(config.get("preprocessor_kwargs") or {}),
    )

    population_size = int(config.get("population_size") or 8)
    epochs = int(config.get("epochs") or 20)
    if config.get("multiobjective", True):
        search.set_moeadd_params(population_size=population_size, training_epochs=epochs)
    else:
        search.set_singleobjective_params(population_size=population_size, training_epochs=epochs)

    return search


def _filter_verbose(requested: dict[str, Any]) -> dict[str, Any]:
    try:
        from epde.globals import init_verbose

        accepted = supported(init_verbose)
    except Exception:  # noqa: BLE001
        return requested
    return {key: value for key, value in requested.items() if key in accepted} or requested


# -------------------------------------------------------------------- the pool


def build_tokens(
    config: dict[str, Any], dimensionality: int, variables: list[str], report: BuildReport
) -> list[Any]:
    """The additional token families the pool should contain."""
    from epde.interface import prepared_tokens

    built: list[Any] = []
    for entry in config.get("token_families") or []:
        family_id = str(entry.get("id") or "")
        descriptor = TOKEN_FAMILY_BY_ID.get(family_id)
        if descriptor is None:
            report.skipped_token_families.append(family_id or "<unnamed>")
            continue
        family_cls = getattr(prepared_tokens, descriptor["class"], None)
        if family_cls is None:
            report.skipped_token_families.append(family_id)
            continue

        params = dict(entry.get("params") or {})
        candidate = _token_kwargs(family_id, params, dimensionality, variables)
        kwargs, dropped = filter_kwargs(family_cls.__init__, candidate)
        if dropped:
            report.notes.append(
                f"Token family '{family_id}' ignored {', '.join(sorted(dropped))} in this EPDE build."
            )
        try:
            built.append(family_cls(**kwargs))
        except Exception as exc:  # noqa: BLE001 - a family that refuses this data
            report.notes.append(f"Token family '{family_id}' could not be built: {exc}")
    return built


def _token_kwargs(
    family_id: str, params: dict[str, Any], dimensionality: int, variables: list[str]
) -> dict[str, Any]:
    if family_id == "trigonometric":
        return {
            "freq": (
                float(params.get("freq_min", 1.5708)),
                float(params.get("freq_max", 6.2832)),
            ),
            "dimensionality": dimensionality,
            "meaningful": bool(params.get("meaningful", False)),
        }
    if family_id == "grid":
        return {
            # One label per family: EPDE's ``dim`` parameter already selects the
            # axis, and one token per axis would only duplicate it.
            "labels": ["x"],
            "max_power": int(params.get("max_power", 1)),
            "dimensionality": dimensionality,
        }
    if family_id in {"polynomial", "sign"}:
        return {
            "var_name": variables[0] if variables else "u",
            "max_power": int(params.get("max_power", 2 if family_id == "polynomial" else 1)),
        }
    if family_id == "phased_sine":
        return {
            "freq": (
                float(params.get("freq_min", 1.5708)),
                float(params.get("freq_max", 6.2832)),
            )
        }
    return dict(params)


# ----------------------------------------------------------------------- fit


def fit_kwargs(
    search: Any,
    config: dict[str, Any],
    data: list[Any],
    variables: list[str],
    tokens: list[Any],
    report: BuildReport,
) -> dict[str, Any]:
    """Keyword arguments for ``EpdeSearch.fit``, trimmed to this build."""
    factors = config.get("equation_factors_max_number")
    if isinstance(factors, dict):
        # EPDE also accepts {'factors_num': [...], 'probas': [...]}, which is how
        # a run asks for mostly-single-factor terms with occasional products.
        factors_value: Any = factors
    else:
        factors_value = int(factors or 1)

    sparsity = (
        float(config.get("sparsity_min", 1e-8)),
        float(config.get("sparsity_max", 1.0)),
    )

    candidate: dict[str, Any] = {
        "data": data,
        "variable_names": list(variables),
        "max_deriv_order": _deriv_order(config),
        "equation_terms_max_number": int(config.get("equation_terms_max_number") or 5),
        "equation_factors_max_number": factors_value,
        "eq_sparsity_interval": sparsity,
        "data_fun_pow": int(config.get("data_fun_pow") or 1),
        "additional_tokens": tokens,
    }
    if config.get("deriv_fun_pow") is not None:
        candidate["deriv_fun_pow"] = int(config["deriv_fun_pow"])

    kwargs, dropped = filter_kwargs(search.fit, candidate)
    report.dropped_fit_kwargs.extend(dropped)
    return kwargs


def _deriv_order(config: dict[str, Any]) -> Any:
    order = config.get("max_deriv_order", 2)
    if isinstance(order, (list, tuple)):
        return tuple(int(value) for value in order)
    return int(order)


def second_axis_name(config: dict[str, Any], report: BuildReport | None = None) -> str:
    """What the second Pareto objective measures in this configuration.

    EPDE master can put either structural complexity or coefficient stability on
    the second axis, chosen by ``use_pic``. The effective value comes from the
    constructed search where one exists, because a run that does not ask gets
    the build's default -- which is ``True`` on master, so assuming "complexity"
    from an unset request would mislabel the chart on every default run.
    """
    use_pic = report.use_pic if report is not None and report.use_pic is not None else config.get("use_pic")
    return "stability" if use_pic else "complexity"
