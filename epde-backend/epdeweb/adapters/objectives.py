"""Pareto bookkeeping.

EPDE minimises a *vector*: the discrepancy of each equation in the system and,
on the second axis, either its complexity or the stability of its coefficients.
There is therefore no single number to sort a population by, which is the one
structural difference between an EPDE genealogy and a FEDOT one -- "the best
individual of this generation" is a set, not an element.

Everything here works on plain lists of floats so it can be used on both sides
of the process boundary: in the worker, where the objects are EPDE systems, and
in the API, where they are values decoded from a stored event.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any

#: All EPDE objectives are minimised, so a lower value is better everywhere in
#: this module. That happens to match GOLEM's internal convention, so the
#: history builder needs no sign handling.
LOWER_IS_BETTER = True


def clean_objectives(values: Iterable[Any] | None) -> list[float] | None:
    """Objective vector as plain floats, or ``None`` if it never evaluated.

    A candidate whose fitness could not be computed carries ``inf`` or ``nan``
    in one slot; that is a failed evaluation, not a very bad system, and
    treating it as a number would flatten the colour scale of the whole graph.
    """
    if values is None:
        return None
    cleaned: list[float] = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number) or math.isinf(number):
            return None
        cleaned.append(number)
    return cleaned or None


def dominates(left: Sequence[float], right: Sequence[float]) -> bool:
    """True when ``left`` is at least as good on every objective and better on one."""
    if len(left) != len(right):
        return False
    better_somewhere = False
    for a, b in zip(left, right, strict=True):
        if a > b:
            return False
        if a < b:
            better_somewhere = True
    return better_somewhere


def non_dominated_levels(population: Sequence[Sequence[float] | None]) -> list[int | None]:
    """Non-domination level of each member; ``None`` for unevaluated members.

    Level 0 is the Pareto front. This is the textbook peeling procedure rather
    than EPDE's own incremental one: it is used on stored payloads, where the
    incremental structure is long gone, and a population is at most a few dozen
    systems.
    """
    levels: list[int | None] = [None] * len(population)
    remaining = [index for index, values in enumerate(population) if values is not None]

    level = 0
    while remaining:
        front = [
            index
            for index in remaining
            if not any(
                dominates(population[other], population[index])  # type: ignore[arg-type]
                for other in remaining
                if other != index
            )
        ]
        if not front:
            # Only reachable if `dominates` were not a strict partial order;
            # bail out rather than loop forever.
            front = list(remaining)
        for index in front:
            levels[index] = level
        remaining = [index for index in remaining if index not in set(front)]
        level += 1

    return levels


def pareto_front_indices(population: Sequence[Sequence[float] | None]) -> list[int]:
    """Indices of the non-dominated members."""
    levels = non_dominated_levels(population)
    return [index for index, level in enumerate(levels) if level == 0]


def summarise_objectives(
    population: Sequence[Sequence[float] | None], names: Sequence[str] | None = None
) -> dict[str, Any]:
    """Per-objective spread of one generation, for the progress chart.

    Reported per objective rather than as one aggregate: the two axes of an
    EPDE search pull against each other, and an average over them would hide
    exactly the trade-off the run is exploring.
    """
    evaluated = [values for values in population if values is not None]
    summary: dict[str, Any] = {
        "size": len(population),
        "evaluated": len(evaluated),
        "objectives": [],
    }
    if not evaluated:
        return summary

    width = min(len(values) for values in evaluated)
    for index in range(width):
        column = [values[index] for values in evaluated]
        summary["objectives"].append(
            {
                "index": index,
                "name": names[index] if names and index < len(names) else f"objective {index}",
                "best": min(column),
                "worst": max(column),
                "mean": sum(column) / len(column),
            }
        )
    summary["front_size"] = len(pareto_front_indices(population))
    return summary


def hypervolume_2d(front: Sequence[Sequence[float]], reference: Sequence[float]) -> float | None:
    """Dominated hypervolume of a two-objective front, as a convergence measure.

    A single number that improves monotonically as the front advances, which is
    what the progress chart needs when the objectives themselves cannot be
    reduced to one. Restricted to two objectives on purpose: EPDE's MOEA/D
    front is two-axis, and a general implementation would be a lot of code for
    a case that does not arise here.
    """
    points = [tuple(values[:2]) for values in front if values is not None and len(values) >= 2]
    points = [point for point in points if point[0] < reference[0] and point[1] < reference[1]]
    if not points:
        return None

    points.sort(key=lambda point: point[0])
    volume = 0.0
    previous_y = reference[1]
    for x, y in points:
        if y >= previous_y:
            # Dominated by an earlier point in this sweep; contributes nothing.
            continue
        volume += (reference[0] - x) * (previous_y - y)
        previous_y = y
    return volume


def default_objective_names(variables: Sequence[str], second_axis: str) -> list[str]:
    """The names EPDE gives the entries of ``SoEq.obj_fun``.

    The vector is one quality value per equation followed by one second-axis
    value per equation, in the order the variables were declared -- that layout
    is shared by every EPDE build supported here. It is only a *default*: the
    worker checks it against the real vector length and falls back to positional
    names when a build lays them out differently.
    """
    return [f"quality: {name}" for name in variables] + [f"{second_axis}: {name}" for name in variables]
