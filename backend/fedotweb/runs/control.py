"""Changing how the evolution behaves while it is running.

GOLEM re-derives several of its own parameters at the start of every generation:
``_update_requirements`` overwrites ``pop_size`` and the mutation and crossover
probabilities from adaptive sources. Assigning to those fields from outside would
therefore last exactly until the next generation began.

So the controls here work at the source. Population size and operator
probabilities are supplied by objects implementing GOLEM's ``AdaptiveParameter``
protocol; wrapping those lets an override survive the adaptive update. The
remaining knobs -- generation count and time budget -- are read live by the
optimiser's stopping conditions and can simply be assigned.

The GUI and the worker are separate processes, so requests travel through a small
JSON file in the run directory, which the worker reads between generations. A
generation is never interrupted mid-flight.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

CONTROL_FILE = "control.json"

#: Bounds applied to whatever the client asks for, so a typo cannot wedge a run.
LIMITS = {
    "pop_size": (2, 500),
    "num_of_generations": (1, 10_000),
    "timeout_minutes": (0.1, 100_000.0),
    "mutation_prob": (0.0, 1.0),
    "crossover_prob": (0.0, 1.0),
}


@dataclass
class EvolutionControls:
    """Values the user has asked for. ``None`` means "leave GOLEM in charge"."""

    pop_size: int | None = None
    num_of_generations: int | None = None
    timeout_minutes: float | None = None
    mutation_prob: float | None = None
    crossover_prob: float | None = None
    #: Stop after the current generation, keeping the best pipeline found so far.
    finish_now: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(name: str, value: Any) -> Any:
    limits = LIMITS.get(name)
    if limits is None or value is None:
        return value
    low, high = limits
    return min(max(value, low), high)


def coerce_patch(patch: dict[str, Any]) -> dict[str, Any]:
    """Keep only known fields, and hold each within its safe range."""
    known = {field.name for field in fields(EvolutionControls)}
    cleaned: dict[str, Any] = {}
    for name, value in patch.items():
        if name not in known:
            continue
        if name == "finish_now":
            cleaned[name] = bool(value)
        elif value is None:
            cleaned[name] = None
        elif name in ("pop_size", "num_of_generations"):
            cleaned[name] = int(_clamp(name, int(value)))
        else:
            cleaned[name] = float(_clamp(name, float(value)))
    return cleaned


def read_controls(run_dir: Path) -> EvolutionControls:
    path = run_dir / CONTROL_FILE
    if not path.exists():
        return EvolutionControls()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A half-written file is transient; the next read picks up the new one.
        return EvolutionControls()
    return EvolutionControls(**coerce_patch(payload))


def write_controls(run_dir: Path, patch: dict[str, Any]) -> EvolutionControls:
    """Merge a patch into the stored controls and return the result."""
    run_dir.mkdir(parents=True, exist_ok=True)
    current = read_controls(run_dir).as_dict()
    current.update(coerce_patch(patch))

    merged = EvolutionControls(**current)
    path = run_dir / CONTROL_FILE
    # Write-then-replace so a reader never sees a partial file.
    staging = path.with_suffix(".json.tmp")
    staging.write_text(json.dumps(merged.as_dict(), ensure_ascii=False), encoding="utf-8")
    staging.replace(path)
    return merged


class OverridableParameter:
    """Wraps a GOLEM ``AdaptiveParameter`` so a fixed value can take over.

    While ``override`` is ``None`` the wrapped policy is untouched, so a run left
    alone behaves exactly as it would without the GUI attached.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.override: Any = None

    @property
    def initial(self) -> Any:
        return self._inner.initial

    def next(self, population: Any) -> Any:
        # The wrapped policy is still advanced, so releasing the override resumes
        # the adaptive schedule from where it would have been.
        value = self._inner.next(population)
        return value if self.override is None else self.override


class OverridableOperatorProbabilities(OverridableParameter):
    """The mutation/crossover pair, each independently overridable."""

    def __init__(self, inner: Any) -> None:
        super().__init__(inner)
        self.mutation_override: float | None = None
        self.crossover_override: float | None = None

    def next(self, population: Any) -> Any:
        mutation, crossover = self._inner.next(population)
        return (
            mutation if self.mutation_override is None else self.mutation_override,
            crossover if self.crossover_override is None else self.crossover_override,
        )


def install_overrides(optimizer: Any) -> None:
    """Replace the optimiser's adaptive parameter sources with overridable ones."""
    if getattr(optimizer, "_fedotweb_overrides", False):
        return
    optimizer._pop_size = OverridableParameter(optimizer._pop_size)
    optimizer._operators_prob = OverridableOperatorProbabilities(optimizer._operators_prob)
    optimizer._fedotweb_overrides = True


def apply_controls(optimizer: Any, controls: EvolutionControls) -> list[str]:
    """Apply the requested controls to a live optimiser.

    Returns a human-readable description of everything that actually changed, so
    the run log can show what took effect and when.
    """
    applied: list[str] = []
    params = optimizer.graph_optimizer_params
    requirements = optimizer.requirements

    if controls.pop_size is not None and optimizer._pop_size.override != controls.pop_size:
        optimizer._pop_size.override = controls.pop_size
        # Also set it directly, so the change lands on the coming generation
        # rather than the one after it.
        params.pop_size = controls.pop_size
        applied.append(f"population size → {controls.pop_size}")
    elif controls.pop_size is None and optimizer._pop_size.override is not None:
        optimizer._pop_size.override = None
        applied.append("population size → adaptive")

    probabilities = optimizer._operators_prob
    if controls.mutation_prob is not None and probabilities.mutation_override != controls.mutation_prob:
        probabilities.mutation_override = controls.mutation_prob
        params.mutation_prob = controls.mutation_prob
        applied.append(f"mutation probability → {controls.mutation_prob:g}")
    elif controls.mutation_prob is None and probabilities.mutation_override is not None:
        probabilities.mutation_override = None
        applied.append("mutation probability → adaptive")

    if controls.crossover_prob is not None and probabilities.crossover_override != controls.crossover_prob:
        probabilities.crossover_override = controls.crossover_prob
        params.crossover_prob = controls.crossover_prob
        applied.append(f"crossover probability → {controls.crossover_prob:g}")
    elif controls.crossover_prob is None and probabilities.crossover_override is not None:
        probabilities.crossover_override = None
        applied.append("crossover probability → adaptive")

    if (
        controls.num_of_generations is not None
        and requirements.num_of_generations != controls.num_of_generations
    ):
        requirements.num_of_generations = controls.num_of_generations
        applied.append(f"generation limit → {controls.num_of_generations}")

    if controls.timeout_minutes is not None:
        wanted = datetime.timedelta(minutes=controls.timeout_minutes)
        if optimizer.timer.timeout != wanted:
            optimizer.timer.timeout = wanted
            requirements.timeout = wanted
            applied.append(f"time budget → {controls.timeout_minutes:g} min")

    if controls.finish_now:
        # Ending through the generation limit lets the optimiser return normally,
        # so FEDOT still fits and hands back the best pipeline it found. Killing
        # the process would throw that away.
        #
        # GOLEM stops once ``current_generation_num >= num_of_generations + 1``,
        # so the limit has to go one below the current generation for the loop to
        # exit at its next check rather than running another whole generation.
        current = int(getattr(optimizer, "current_generation_num", 0))
        target = max(0, current - 1)
        if requirements.num_of_generations is None or requirements.num_of_generations > target:
            requirements.num_of_generations = target
            applied.append("finishing now, keeping the best result so far")

    return applied


def describe_effective(optimizer: Any) -> dict[str, Any]:
    """What the optimiser is currently using, for display next to the controls."""
    params = optimizer.graph_optimizer_params
    requirements = optimizer.requirements
    timeout = getattr(optimizer.timer, "timeout", None)
    return {
        "pop_size": getattr(params, "pop_size", None),
        "mutation_prob": getattr(params, "mutation_prob", None),
        "crossover_prob": getattr(params, "crossover_prob", None),
        "num_of_generations": getattr(requirements, "num_of_generations", None),
        "timeout_minutes": timeout.total_seconds() / 60 if timeout else None,
        "max_depth": getattr(requirements, "max_depth", None),
        "generation": int(getattr(optimizer, "current_generation_num", 0)),
    }
