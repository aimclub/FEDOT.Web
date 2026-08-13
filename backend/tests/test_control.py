"""Changing the evolution while it runs.

GOLEM re-derives population size and operator probabilities at the start of every
generation, so these tests pin down the part that is easy to get wrong: an
override has to survive that update, and releasing it has to hand control back.
"""

from __future__ import annotations

import datetime
from types import SimpleNamespace

import pytest

from fedotweb.runs.control import (
    EvolutionControls,
    apply_controls,
    coerce_patch,
    describe_effective,
    install_overrides,
    read_controls,
    write_controls,
)


class FakeAdaptive:
    """Stands in for GOLEM's adaptive parameter: a value that drifts each call."""

    def __init__(self, start: int = 10) -> None:
        self._value = start

    @property
    def initial(self):
        return self._value

    def next(self, _population):
        self._value += 1
        return self._value


class FakeProbabilities:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def initial(self):
        return (0.8, 0.8)

    def next(self, _population):
        self.calls += 1
        return (0.8, 0.8)


def make_optimizer(generation: int = 3):
    optimizer = SimpleNamespace(
        graph_optimizer_params=SimpleNamespace(pop_size=10, mutation_prob=0.8, crossover_prob=0.8),
        requirements=SimpleNamespace(num_of_generations=40, timeout=None, max_depth=5),
        timer=SimpleNamespace(timeout=datetime.timedelta(minutes=10)),
        current_generation_num=generation,
    )
    optimizer._pop_size = FakeAdaptive()
    optimizer._operators_prob = FakeProbabilities()
    install_overrides(optimizer)
    return optimizer


# ---------------------------------------------------------------------- patches


def test_unknown_fields_are_dropped_and_values_clamped() -> None:
    cleaned = coerce_patch(
        {"pop_size": 10_000, "mutation_prob": 5.0, "nonsense": 1, "finish_now": "yes"}
    )
    assert cleaned["pop_size"] == 500  # upper bound
    assert cleaned["mutation_prob"] == 1.0
    assert cleaned["finish_now"] is True
    assert "nonsense" not in cleaned


def test_controls_round_trip_through_the_run_directory(tmp_path) -> None:
    assert read_controls(tmp_path) == EvolutionControls()

    write_controls(tmp_path, {"pop_size": 24})
    write_controls(tmp_path, {"mutation_prob": 0.3})

    stored = read_controls(tmp_path)
    assert stored.pop_size == 24
    assert stored.mutation_prob == pytest.approx(0.3)


def test_a_corrupt_control_file_is_ignored(tmp_path) -> None:
    """A half-written file must not take the run down."""
    (tmp_path / "control.json").write_text("{not json", encoding="utf-8")
    assert read_controls(tmp_path) == EvolutionControls()


# --------------------------------------------------------------------- applying


def test_population_override_survives_the_adaptive_update() -> None:
    """The whole point: GOLEM would otherwise overwrite this next generation."""
    optimizer = make_optimizer()
    apply_controls(optimizer, EvolutionControls(pop_size=24))

    assert optimizer.graph_optimizer_params.pop_size == 24
    # What GOLEM asks for on the following generations.
    assert optimizer._pop_size.next(None) == 24
    assert optimizer._pop_size.next(None) == 24


def test_releasing_an_override_returns_control_to_golem() -> None:
    optimizer = make_optimizer()
    apply_controls(optimizer, EvolutionControls(pop_size=24))
    changes = apply_controls(optimizer, EvolutionControls(pop_size=None))

    assert any("adaptive" in change for change in changes)
    # The wrapped policy kept advancing underneath, so it resumes where it was.
    assert optimizer._pop_size.next(None) != 24


def test_operator_probabilities_are_independently_overridable() -> None:
    optimizer = make_optimizer()
    apply_controls(optimizer, EvolutionControls(mutation_prob=0.35))

    mutation, crossover = optimizer._operators_prob.next(None)
    assert mutation == pytest.approx(0.35)
    assert crossover == pytest.approx(0.8), "crossover must stay with GOLEM"

    apply_controls(optimizer, EvolutionControls(mutation_prob=0.35, crossover_prob=0.15))
    mutation, crossover = optimizer._operators_prob.next(None)
    assert (mutation, crossover) == (pytest.approx(0.35), pytest.approx(0.15))


def test_generation_limit_and_time_budget_are_assigned() -> None:
    optimizer = make_optimizer()
    changes = apply_controls(
        optimizer, EvolutionControls(num_of_generations=99, timeout_minutes=20)
    )

    assert optimizer.requirements.num_of_generations == 99
    assert optimizer.timer.timeout == datetime.timedelta(minutes=20)
    assert len(changes) == 2


def test_reapplying_the_same_controls_reports_no_change() -> None:
    """The run log should not fill with repeats of a setting that already holds."""
    optimizer = make_optimizer()
    controls = EvolutionControls(pop_size=24, num_of_generations=99)

    assert apply_controls(optimizer, controls)
    assert apply_controls(optimizer, controls) == []


def test_finish_now_trips_the_stopping_condition() -> None:
    """GOLEM stops at `current >= num_of_generations + 1`, so the limit must go below."""
    optimizer = make_optimizer(generation=7)
    changes = apply_controls(optimizer, EvolutionControls(finish_now=True))

    assert optimizer.requirements.num_of_generations == 6
    assert optimizer.current_generation_num >= optimizer.requirements.num_of_generations + 1
    assert any("keeping the best result" in change for change in changes)


def test_installing_overrides_twice_does_not_nest_them() -> None:
    optimizer = make_optimizer()
    inner = optimizer._pop_size
    install_overrides(optimizer)
    assert optimizer._pop_size is inner


def test_effective_description_reports_what_is_in_force() -> None:
    optimizer = make_optimizer(generation=4)
    apply_controls(optimizer, EvolutionControls(pop_size=24, timeout_minutes=20))

    described = describe_effective(optimizer)
    assert described["pop_size"] == 24
    assert described["generation"] == 4
    assert described["timeout_minutes"] == pytest.approx(20.0)
