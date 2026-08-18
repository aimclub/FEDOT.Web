"""Extraction of machine-readable hyperparameter schemas from FEDOT.

FEDOT already knows, for every operation, which hyperparameters exist, what type
they are and which values are admissible -- that knowledge lives in
``PipelineSearchSpace`` (used by the tuner) and in ``default_operation_params.json``.
The legacy web GUI ignored all of it and rendered every hyperparameter as a bare
text field.  This module turns that knowledge into JSON so the UI can render a
proper typed editor: a slider bounded by the real sampling scope for continuous
parameters, an integer stepper for discrete ones, a dropdown for categorical ones.

Three sources are merged per operation:

* ``PipelineSearchSpace``            -- type, sampling scope, hyperopt distribution
* ``DefaultOperationParamsRepository`` -- default value applied when the node is created
* the operation repositories        -- tags, supported tasks, input/output data types
"""

from __future__ import annotations

import math
from typing import Any

from fedot.core.pipelines.tuning.search_space import PipelineSearchSpace
from fedot.core.repository.default_params_repository import DefaultOperationParamsRepository
from fedot.core.utils import NESTED_PARAMS_LABEL

#: Distributions whose sampling scope is best explored on a logarithmic axis.
LOG_SCALE_DISTRIBUTIONS = frozenset({"loguniform", "qloguniform", "lognormal"})

#: ``hyperopt`` distributions that draw from an explicit list of options.
CHOICE_DISTRIBUTIONS = frozenset({"choice"})


def _distribution_name(dist: Any) -> str | None:
    """Return the readable name of a ``hyperopt`` distribution callable.

    ``hp.uniform`` and friends are defined as ``hp_uniform`` internally, so the
    prefix is stripped to give the plain distribution name.
    """
    if dist is None:
        return None
    name = getattr(dist, "__name__", None)
    if not name:
        # ``functools.partial`` wrappers are used for a few operations.
        inner = getattr(dist, "func", None)
        name = getattr(inner, "__name__", None) if inner is not None else None
    if not name:
        return None
    return name[3:] if name.startswith("hp_") else name


def _literal_value(node: Any) -> Any:
    """Unwrap a ``hyperopt`` literal node into a plain Python value.

    Returns the node untouched when it is already a plain value.
    """
    obj = getattr(node, "obj", None)
    if obj is not None and type(node).__name__ == "Literal":
        return obj
    return node


def _choices_from_hyperopt(node: Any) -> list[Any] | None:
    """Best-effort extraction of the option list from an ``hp.choice`` expression.

    ``hp.choice(label, options)`` expands into a ``switch`` apply node whose
    positional arguments are the label expression followed by one literal per
    option.  Anything we cannot decode returns ``None`` so the caller can fall
    back to treating the value as opaque.
    """
    pos_args = getattr(node, "pos_args", None)
    if not pos_args or len(pos_args) < 2:
        return None
    options = []
    for arg in pos_args[1:]:
        value = _literal_value(arg)
        if type(value).__name__ in {"Apply", "Literal"}:
            return None
        options.append(value)
    return options


def _is_hyperopt_expression(value: Any) -> bool:
    return type(value).__name__ in {"Apply", "Literal"}


def _json_safe(value: Any) -> Any:
    """Make a value safe for ``json.dumps`` with ``allow_nan=False``.

    FEDOT defaults contain ``inf``/``nan`` in a few places; JSON has no literal
    for either, and the legacy backend worked around this by string-replacing
    ``Infinity`` in already-serialised payloads.
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    # numpy scalars and anything else exotic
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except (ValueError, TypeError):
            pass
    return str(value)


def _value_type(default: Any, param_type: str, choices: list[Any] | None) -> str:
    """Infer the widget-level value type for a parameter."""
    sample = default
    if sample is None and choices:
        sample = next((c for c in choices if c is not None), None)

    if isinstance(sample, bool):
        return "boolean"
    if isinstance(sample, int):
        return "integer"
    if isinstance(sample, float):
        return "number"
    if isinstance(sample, str):
        return "string"
    if isinstance(sample, (list, tuple)):
        return "array"
    if isinstance(sample, dict):
        return "object"

    # No usable sample -- fall back to the declared search-space type.
    if param_type == "discrete":
        return "integer"
    if param_type == "continuous":
        return "number"
    return "string"


def _parse_nested_variants(scope: Any) -> list[dict[str, Any]]:
    """Decode the ``nested_space`` entry used by operations such as ``glm``.

    The scope is a list of dicts; each dict fixes some fields to literals and
    leaves others as ``hp.choice`` expressions over sub-options.
    """
    variants: list[dict[str, Any]] = []
    if not isinstance(scope, list):
        return variants

    for index, option in enumerate(scope):
        if not isinstance(option, dict):
            continue
        fixed: dict[str, Any] = {}
        options: dict[str, list[Any]] = {}
        for key, value in option.items():
            if _is_hyperopt_expression(value):
                decoded = _choices_from_hyperopt(value)
                if decoded is not None:
                    options[key] = _json_safe(decoded)
            else:
                fixed[key] = _json_safe(value)
        label = str(next(iter(fixed.values()), f"option {index + 1}"))
        variants.append({"label": label, "fixed": fixed, "options": options})
    return variants


def _schema_from_search_space(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Convert one ``PipelineSearchSpace`` entry into a UI-ready parameter schema."""
    param_type = spec.get("type", "categorical")
    distribution = _distribution_name(spec.get("hyperopt-dist"))
    raw_scope = spec.get("sampling-scope") or []

    schema: dict[str, Any] = {
        "name": name,
        "type": param_type,
        "tunable": True,
        "distribution": distribution,
        "log_scale": distribution in LOG_SCALE_DISTRIBUTIONS,
        "default": None,
        "minimum": None,
        "maximum": None,
        "choices": None,
        "nested_variants": None,
    }

    if name == NESTED_PARAMS_LABEL:
        # ``sampling-scope`` is wrapped in an extra list for choice distributions.
        inner = raw_scope[0] if len(raw_scope) == 1 else raw_scope
        schema["type"] = "nested"
        schema["nested_variants"] = _parse_nested_variants(inner)
        schema["value_type"] = "object"
        return schema

    if param_type == "categorical" or distribution in CHOICE_DISTRIBUTIONS:
        # Choice scopes are given as ``[[option, option, ...]]``.
        options = raw_scope[0] if len(raw_scope) == 1 and isinstance(raw_scope[0], (list, tuple)) else raw_scope
        decoded = [_json_safe(o) for o in options if not _is_hyperopt_expression(o)]
        schema["choices"] = decoded or None
    elif len(raw_scope) >= 2:
        low, high = raw_scope[0], raw_scope[1]
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            schema["minimum"] = _json_safe(low)
            schema["maximum"] = _json_safe(high)

    schema["value_type"] = _value_type(None, schema["type"], schema.get("choices"))
    return schema


def _schema_from_default(name: str, value: Any) -> dict[str, Any]:
    """Build a schema for a parameter that has a default but no search-space entry.

    These are still editable -- they are simply not explored by the tuner -- so
    the UI needs to know their type in order to render the right widget.
    """
    safe = _json_safe(value)
    value_type = _value_type(safe, "categorical", None)
    return {
        "name": name,
        "type": "boolean" if value_type == "boolean" else "free",
        "tunable": False,
        "distribution": None,
        "log_scale": False,
        "default": safe,
        "minimum": None,
        "maximum": None,
        "choices": [True, False] if value_type == "boolean" else None,
        "nested_variants": None,
        "value_type": value_type,
    }


class HyperparameterCatalog:
    """Merged view over FEDOT's search space and default-parameter repositories."""

    def __init__(self) -> None:
        self._search_space = PipelineSearchSpace().parameters_per_operation
        self._defaults_repo = DefaultOperationParamsRepository()

    @staticmethod
    def _base_name(operation: str) -> str:
        """Strip the ``/variant`` suffix some operation ids carry (e.g. ``lagged/1``)."""
        return operation.split("/")[0]

    @property
    def operations_with_search_space(self) -> list[str]:
        return sorted(self._search_space.keys())

    def defaults_for(self, operation: str) -> dict[str, Any]:
        """Default hyperparameter values FEDOT applies to a freshly created node."""
        params = self._defaults_repo.get_default_params_for_operation(operation)
        return _json_safe(dict(params)) if isinstance(params, dict) else {}

    def schema_for(self, operation: str) -> list[dict[str, Any]]:
        """Typed schemas for every hyperparameter of ``operation``.

        Parameters present in the tuner's search space come first (those are the
        ones evolution actually varies), followed by parameters that only have a
        default value.
        """
        defaults = self.defaults_for(operation)
        space = self._search_space.get(operation) or self._search_space.get(self._base_name(operation), {})

        schemas: list[dict[str, Any]] = []
        for name, spec in space.items():
            if not isinstance(spec, dict):
                continue
            schema = _schema_from_search_space(name, spec)
            if name in defaults:
                schema["default"] = defaults[name]
                # A concrete default is a better type hint than the declared type.
                schema["value_type"] = _value_type(defaults[name], schema["type"], schema.get("choices"))
            schemas.append(schema)

        covered = {s["name"] for s in schemas}
        for name, value in defaults.items():
            if name not in covered:
                schemas.append(_schema_from_default(name, value))

        return schemas
