"""Steering an EPDE search while it runs.

FEDOT.Web can change population size, operator probabilities and the generation
limit mid-run because GOLEM re-reads them from its requirements object every
generation. EPDE has no such object: each evolutionary operator owns a ``params``
dict, populated once from ``default_parameters_*.json`` and read on every
application. That is enough -- writing into those dicts between generations
changes the next generation's behaviour, and nothing in EPDE recomputes them --
so the controls here find the live operator instances and assign to them.

Two limits are structural rather than oversights, and are reported as such:

* **Population size is fixed.** MOEA/D pairs every individual with a weight
  vector generated at construction; changing the population would leave sectors
  without owners. Only the single-objective optimiser could grow, and it takes
  its size from the same construction-time argument.
* **The epoch count cannot be lowered inside EPDE.** ``MOEADDOptimizer.optimize``
  iterates ``np.arange(epochs)`` captured at entry. A lower limit is therefore
  enforced from the outside, by the observer, which stops the run after the
  current generation -- the same distinction FEDOT.Web draws between *stop*
  (kill the worker, lose the result) and *finish now* (return through the normal
  path with the population intact).

The GUI and the worker are separate processes, so requests travel through a
small JSON file in the run directory, exactly as they do for FEDOT.Web.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTROLS_FILE = "controls.json"


@dataclass(frozen=True)
class ControlSpec:
    """One knob the GUI offers, and where it lands inside EPDE."""

    name: str
    #: ``CompoundOperator.key`` values that carry the parameter. Several are
    #: listed because the single- and multi-objective operator sets are separate
    #: class hierarchies that happen to share parameter names.
    operator_keys: tuple[str, ...]
    parameter: str
    label: str
    description: str
    minimum: float
    maximum: float


#: Every parameter here is read by its operator on each application, so a change
#: takes effect on the next generation and never disturbs one in flight.
CONTROL_SPECS: tuple[ControlSpec, ...] = (
    ControlSpec(
        name="mutation_prob",
        operator_keys=("SystemMutation",),
        parameter="indiv_mutation_prob",
        label="Mutation probability",
        description="Chance that an individual equation of a system is mutated at all.",
        minimum=0.0,
        maximum=1.0,
    ),
    ControlSpec(
        name="equation_mutation_rate",
        operator_keys=("EquationMutation",),
        parameter="r_mutation",
        label="Terms mutated",
        description="Fraction of an equation's terms considered for replacement.",
        minimum=0.0,
        maximum=1.0,
    ),
    ControlSpec(
        name="term_addition_prob",
        operator_keys=("EquationMutation",),
        parameter="term_addition_prob",
        label="Term addition",
        description="Chance a mutation adds a term rather than replacing one.",
        minimum=0.0,
        maximum=1.0,
    ),
    ControlSpec(
        name="crossover_prob",
        operator_keys=("TermCrossover",),
        parameter="crossover_probability",
        label="Term exchange",
        description="Chance that two parents swap a whole term during crossover.",
        minimum=0.0,
        maximum=1.0,
    ),
    ControlSpec(
        name="parents_fraction",
        operator_keys=("MOEADDSelection", "RouletteWheelSelection"),
        parameter="parents_fraction",
        label="Parents fraction",
        description="Share of the population selected to breed each generation.",
        minimum=0.01,
        maximum=1.0,
    ),
    ControlSpec(
        name="term_param_mutation_rate",
        operator_keys=("TermParameterMutation",),
        parameter="r_param_mutation",
        label="Token parameters mutated",
        description="Fraction of token parameters (frequency, power) that drift.",
        minimum=0.0,
        maximum=1.0,
    ),
)

CONTROL_BY_NAME = {spec.name: spec for spec in CONTROL_SPECS}


@dataclass
class Controls:
    """What has been asked for. ``None`` means "leave EPDE's own value alone"."""

    values: dict[str, float]
    #: Stop after the current generation, keeping the population found so far.
    finish_now: bool = False
    #: A lower epoch limit than the run started with, enforced by the observer.
    epochs: int | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {name: None for name in CONTROL_BY_NAME}
        payload.update(self.values)
        payload["finish_now"] = self.finish_now
        payload["epochs"] = self.epochs
        return payload


def read_controls(run_dir: Path) -> Controls:
    path = run_dir / CONTROLS_FILE
    if not path.exists():
        return Controls(values={})
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A half-written file is momentary; the next generation reads it again.
        return Controls(values={})
    if not isinstance(raw, dict):
        return Controls(values={})

    values: dict[str, float] = {}
    for name, spec in CONTROL_BY_NAME.items():
        value = raw.get(name)
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        values[name] = min(max(number, spec.minimum), spec.maximum)

    epochs = raw.get("epochs")
    try:
        epochs = int(epochs) if epochs is not None else None
    except (TypeError, ValueError):
        epochs = None

    return Controls(values=values, finish_now=bool(raw.get("finish_now", False)), epochs=epochs)


def write_controls(run_dir: Path, patch: dict[str, Any]) -> Controls:
    """Merge a patch into the request file. Absent keys keep their value."""
    run_dir.mkdir(parents=True, exist_ok=True)
    current = read_controls(run_dir).as_dict()
    for key, value in patch.items():
        if key in CONTROL_BY_NAME or key in {"finish_now", "epochs"}:
            current[key] = value
    (run_dir / CONTROLS_FILE).write_text(
        json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return read_controls(run_dir)


# ------------------------------------------------------- live operator lookup


def collect_operators(root: Any) -> dict[str, list[Any]]:
    """Every evolutionary operator reachable from a strategy, keyed by its key.

    EPDE assembles the strategy as blocks holding compound operators, each of
    which holds suboperators, so the live instances -- the ones whose ``params``
    an application actually reads -- are several levels down and are the only
    ones worth writing to.
    """
    found: dict[str, list[Any]] = {}
    seen: set[int] = set()

    def walk(operator: Any) -> None:
        if operator is None or id(operator) in seen:
            return
        seen.add(id(operator))
        key = getattr(operator, "key", None)
        if isinstance(key, str) and hasattr(operator, "params"):
            found.setdefault(key, []).append(operator)
        suboperators = getattr(operator, "suboperators", None)
        if suboperators is None:
            return
        try:
            children = list(suboperators)
        except TypeError:  # pragma: no cover - an operator with no suboperators
            return
        for child in children:
            # A never-populated container iterates its keys, which are strings.
            if not isinstance(child, str):
                walk(child)

    blocks = getattr(getattr(root, "linked_blocks", None), "blocks_labeled", None)
    if isinstance(blocks, dict):
        for block in blocks.values():
            walk(getattr(block, "_operator", None))
    else:
        walk(root)
    return found


def apply_controls(operators: dict[str, list[Any]], controls: Controls) -> list[str]:
    """Write the requested values into the live operators.

    Returns a description of what actually changed, so the GUI can show that a
    request was honoured rather than merely recorded -- an operator that this
    EPDE build does not have (``term_addition_prob`` exists only on master)
    silently accepts nothing otherwise.
    """
    changes: list[str] = []
    for name, value in controls.values.items():
        spec = CONTROL_BY_NAME[name]
        for key in spec.operator_keys:
            for operator in operators.get(key, ()):
                params = getattr(operator, "params", None)
                if not isinstance(params, dict) or spec.parameter not in params:
                    continue
                if _close(params[spec.parameter], value):
                    continue
                params[spec.parameter] = value
                changes.append(f"{spec.label}: {value:g}")
    return changes


def describe_effective(operators: dict[str, list[Any]]) -> dict[str, Any]:
    """What the operators are currently using, read back from the instances."""
    effective: dict[str, Any] = {}
    for name, spec in CONTROL_BY_NAME.items():
        effective[name] = None
        for key in spec.operator_keys:
            for operator in operators.get(key, ()):
                params = getattr(operator, "params", None)
                if isinstance(params, dict) and spec.parameter in params:
                    try:
                        effective[name] = float(params[spec.parameter])
                    except (TypeError, ValueError):
                        effective[name] = None
                    break
            if effective[name] is not None:
                break
    return effective


def describe_specs() -> list[dict[str, Any]]:
    """The control catalogue, so the GUI does not hard-code the knobs."""
    return [
        {
            "name": spec.name,
            "label": spec.label,
            "description": spec.description,
            "minimum": spec.minimum,
            "maximum": spec.maximum,
            "operators": list(spec.operator_keys),
            "parameter": spec.parameter,
        }
        for spec in CONTROL_SPECS
    ]


def _close(left: Any, right: float) -> bool:
    try:
        return abs(float(left) - right) < 1e-12
    except (TypeError, ValueError):
        return False
