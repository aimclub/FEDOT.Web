"""What a discovered equation actually rests on.

FEDOT.Web answers this for a pipeline with GOLEM's structural analysis: delete
each node, refit, and see whether the score got better. The same question for an
equation is cheaper and sharper -- an equation is linear in its coefficients, so
removing a term needs no refit at all. The residual with the term dropped can be
read straight off the same design matrix EPDE already built to fit it.

The number reported is the factor by which the residual grows when a term is
removed. Above 1 the equation depends on the term; at 1 the term is carrying
nothing and only inflates the complexity objective, which is exactly the
situation a sparsity interval is meant to prevent and does not always.

This runs inside the worker, where the token cache and the grids are still
alive. Doing it later, out of process, would mean rebuilding the whole pool.

One honest caveat, reported alongside the numbers: EPDE evaluates its own
fitness through the weak-derivative test function, which suppresses the domain
boundary. The residuals here are unweighted, so the ratios are comparable with
each other but not with the objective value on the Pareto chart.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .structures import equation_weights


def _unpack_evaluation(result: Any) -> tuple[Any, Any]:
    """``(target, features)`` from ``Equation.evaluate``, across EPDE builds.

    Master returns ``(value, target, features)``; earlier releases returned
    ``(target, features)``. Unpacking positionally against the wrong one gives
    a features matrix where the target should be, which produces plausible
    nonsense rather than an error.
    """
    if isinstance(result, tuple):
        if len(result) == 3:
            return result[1], result[2]
        if len(result) == 2:
            return result[0], result[1]
    raise TypeError(f"Unexpected return from Equation.evaluate: {type(result)}")


def _rms(values: Any) -> float:
    array = np.asarray(values, dtype=float).reshape(-1)
    if array.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(array))))


def equation_ablation(equation: Any) -> dict[str, Any]:
    """Per-term dependence of one fitted equation.

    Always returns a report. When the numbers cannot be produced it carries an
    ``error`` saying why -- returning nothing would leave an empty panel in the
    GUI with no way to tell "this term matters to nothing" from "this could not
    be computed", and the second is the one worth knowing about.
    """
    variable = str(getattr(equation, "main_var_to_explain", "") or "")

    if not getattr(equation, "weights_final_evald", False):
        return _failed(variable, "The equation was never fitted, so it has no coefficients.")

    structure = list(getattr(equation, "structure", None) or [])
    target_index = getattr(equation, "target_idx", None)
    if not isinstance(target_index, int) or not (0 <= target_index < len(structure)):
        return _failed(variable, "No right-hand side term has been selected for this equation.")

    coefficient_list, intercept_value = equation_weights(equation, len(structure))
    if coefficient_list is None:
        return _failed(
            variable,
            "The coefficient vector does not match the number of terms, so this EPDE "
            "build stores them in a layout this adapter does not recognise.",
        )

    try:
        target, features = _unpack_evaluation(equation.evaluate(normalize=True, return_val=False))
    except Exception as exc:  # noqa: BLE001 - tokens that no longer evaluate
        return _failed(variable, f"The equation could not be re-evaluated: {exc}")

    target = np.asarray(target, dtype=float).reshape(-1)
    feature_indexes = [index for index in range(len(structure)) if index != target_index]
    if features is None:
        matrix = np.zeros((target.size, 0), dtype=float)
    else:
        matrix = np.asarray(features, dtype=float)
        if matrix.ndim == 1:
            matrix = matrix.reshape(-1, 1)
        if matrix.shape[0] != target.size and matrix.shape[-1] == target.size:
            matrix = matrix.T

    coefficients = np.asarray(coefficient_list, dtype=float)
    intercept = float(intercept_value or 0.0)
    if matrix.shape[1] != coefficients.size:
        # The design matrix and the weight vector disagree, which means this
        # build lays the two out differently. Any ablation computed from them
        # would attribute terms to the wrong coefficients -- plausible numbers,
        # entirely wrong -- so it is refused rather than guessed.
        return _failed(
            variable,
            f"The design matrix has {matrix.shape[1]} columns for "
            f"{coefficients.size} coefficients; this EPDE build orders them differently.",
        )

    prediction = matrix @ coefficients + intercept if coefficients.size else np.full_like(target, intercept)
    residual = target - prediction
    baseline = _rms(residual)
    target_scale = _rms(target)

    entries: list[dict[str, Any]] = []
    for position, structure_index in enumerate(feature_indexes):
        coefficient = float(coefficients[position])
        column = matrix[:, position]
        contribution = coefficient * column
        without = residual + contribution
        grown = _rms(without)
        entries.append(
            {
                "term_id": f"t{structure_index}",
                "index": structure_index,
                "name": str(getattr(structure[structure_index], "name", "") or ""),
                "coefficient": coefficient,
                "active": abs(coefficient) > 0.0,
                # What the equation would be left explaining without this term,
                # measured against the left-hand side. This is the primary
                # number because it is always defined: an equation that fits
                # exactly has a zero residual, and a ratio against zero -- which
                # is exactly the case for the best result a search can produce --
                # would leave the panel empty for the answer that matters most.
                "residual_without": _ratio(grown, target_scale),
                # How much larger the residual gets. 1.0 means the term
                # contributes nothing; ``None`` when the fit is already exact.
                "residual_ratio": _ratio(grown, baseline),
                # How big the term is next to the left-hand side, which explains
                # a large ratio on a term with a tiny coefficient.
                "magnitude": _ratio(_rms(contribution), target_scale),
            }
        )

    entries.sort(key=lambda entry: entry["residual_without"] or 0.0, reverse=True)
    return {
        "variable": variable,
        "error": None,
        "target_term": f"t{target_index}",
        "target_name": str(getattr(structure[target_index], "name", "") or ""),
        "residual_rms": baseline,
        "target_rms": target_scale,
        "relative_residual": _ratio(baseline, target_scale),
        "intercept": intercept,
        "terms": entries,
    }


def _failed(variable: str, reason: str) -> dict[str, Any]:
    return {
        "variable": variable,
        "error": reason,
        "target_term": "",
        "target_name": "",
        "residual_rms": 0.0,
        "target_rms": 0.0,
        "relative_residual": None,
        "intercept": 0.0,
        "terms": [],
    }


def system_ablation(system: Any) -> list[dict[str, Any]]:
    """Per-equation ablation for a whole candidate system."""
    reports: list[dict[str, Any]] = []
    variables = getattr(system, "vars_to_describe", None) or []
    chromosome = getattr(system, "vals", None)
    for variable in variables:
        equation = None
        if chromosome is not None:
            try:
                equation = chromosome[variable]
            except Exception as exc:  # noqa: BLE001
                reports.append(_failed(str(variable), f"The equation could not be read: {exc}"))
                continue
        if equation is None:
            reports.append(_failed(str(variable), "The system holds no equation for this variable."))
            continue
        report = equation_ablation(equation)
        # The chromosome key is which equation this is; the equation's own
        # ``main_var_to_explain`` is only a hint and can lag a mutation.
        report["variable"] = str(variable)
        reports.append(report)
    return reports


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or math.isnan(denominator):
        return None
    value = numerator / denominator
    return None if math.isnan(value) or math.isinf(value) else value
