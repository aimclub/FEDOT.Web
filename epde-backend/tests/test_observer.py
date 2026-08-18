"""The per-generation callback, exercised against a stand-in EPDE.

The observer works by patching EPDE's own classes, so testing it needs those
classes to exist -- but not to be EPDE's. A stand-in package with the same
module paths and the same call shapes puts the whole instrumentation path under
test on a machine with no framework installed, which is where most of this code
will be read and changed.
"""

from __future__ import annotations

import copy
import sys
import types
from pathlib import Path

import pytest

from epdeweb.adapters.controls import write_controls
from epdeweb.adapters.observer import EvolutionObserver, FinishRequested

from .conftest import make_system

MODULE_PATHS = (
    "epde",
    "epde.operators",
    "epde.operators.multiobjective",
    "epde.operators.multiobjective.variation",
    "epde.operators.multiobjective.mutations",
    "epde.operators.multiobjective.moeadd_specific",
    "epde.operators.singleobjective",
    "epde.operators.singleobjective.variation",
    "epde.operators.singleobjective.mutations",
    "epde.optimizers",
    "epde.optimizers.blocks",
    "epde.optimizers.moeadd",
    "epde.optimizers.moeadd.moeadd",
    "epde.optimizers.moeadd.strategy_elems",
    "epde.optimizers.single_criterion",
    "epde.optimizers.single_criterion.optimizer",
)


class ChromosomeCrossover:
    """Mirrors the call shape: takes two parents, returns two offspring."""

    key = "ChromosomeCrossover"

    def apply(self, objective, arguments):
        return copy.deepcopy(objective[0]), copy.deepcopy(objective[1])


class SystemMutation:
    """Mirrors the multi-objective build, which mutates in place."""

    key = "SystemMutation"

    def apply(self, objective, arguments):
        return objective


class CopyingSystemMutation(SystemMutation):
    """Mirrors the single-objective build, which copies first."""

    def apply(self, objective, arguments):
        return copy.deepcopy(objective)


class InitialParetoLevelSorting:
    key = "InitialParetoLevelSorting"

    def apply(self, objective, arguments):
        return objective


class MOEADDSectorProcesser:
    def run(self, population_subset, EA_kwargs):  # noqa: N803 - mirrors EPDE
        return population_subset


class LinkedBlocks:
    def __init__(self, output):
        self.output = output

    def traversal(self, input_obj, EA_kwargs):  # noqa: N803 - mirrors EPDE
        return None


class MOEADDOptimizer:
    def __init__(self, levels, weights):
        self.pareto_levels = levels
        self.weights = weights
        self.sector_processer = None

    def set_strategy(self, strategy_director):
        return None


class SimpleOptimizer:
    def __init__(self, population):
        self.population = population
        self.strategy = None

    def set_strategy(self, strategy_director):
        return None


class ParetoLevels:
    def __init__(self, population, front):
        self.population = list(population)
        self.levels = [list(front)]


@pytest.fixture()
def fake_epde(monkeypatch: pytest.MonkeyPatch):
    """Install a stand-in ``epde`` package for the duration of one test."""
    modules = {}
    for path in MODULE_PATHS:
        modules[path] = types.ModuleType(path)
    modules["epde.operators.multiobjective.variation"].ChromosomeCrossover = ChromosomeCrossover
    modules["epde.operators.singleobjective.variation"].ChromosomeCrossover = ChromosomeCrossover
    modules["epde.operators.multiobjective.mutations"].SystemMutation = SystemMutation
    modules["epde.operators.singleobjective.mutations"].SystemMutation = CopyingSystemMutation
    modules["epde.operators.multiobjective.moeadd_specific"].InitialParetoLevelSorting = (
        InitialParetoLevelSorting
    )
    modules["epde.optimizers.moeadd.strategy_elems"].MOEADDSectorProcesser = MOEADDSectorProcesser
    modules["epde.optimizers.blocks"].LinkedBlocks = LinkedBlocks
    modules["epde.optimizers.moeadd.moeadd"].MOEADDOptimizer = MOEADDOptimizer
    modules["epde.optimizers.single_criterion.optimizer"].SimpleOptimizer = SimpleOptimizer

    for path, module in modules.items():
        monkeypatch.setitem(sys.modules, path, module)
    yield modules


def collect(events: list[tuple[str, dict]], kind: str) -> list[dict]:
    return [payload for name, payload in events if name == kind]


@pytest.fixture()
def recorder():
    events: list[tuple[str, dict]] = []

    def emit(kind, **payload):
        events.append((kind, payload))

    return events, emit


def test_an_epoch_boundary_is_found_by_counting_sector_runs(fake_epde, recorder):
    """EPDE's multi-objective loop has no per-epoch hook.

    Counting sector runs against the number of weight vectors recovers the
    boundary without depending on anything inside ``optimize``, which differs
    between builds.
    """
    events, emit = recorder
    observer = EvolutionObserver(multiobjective=True, emit=emit).install()
    try:
        population = [make_system() for _ in range(3)]
        levels = ParetoLevels(population, population[:1])
        optimizer = MOEADDOptimizer(levels, weights=[0, 1, 2])
        optimizer.set_strategy(None)

        processer = MOEADDSectorProcesser()
        for _ in range(6):  # two epochs of three sectors
            processer.run(levels, {})
    finally:
        observer.uninstall()

    generations = collect(events, "generation")
    assert [entry["label"] for entry in generations] == ["gen 1", "gen 2"]
    assert collect(events, "progress")  # the sectors in between are reported too


def test_the_seed_population_is_reported_before_evolution(fake_epde, recorder):
    events, emit = recorder
    observer = EvolutionObserver(multiobjective=True, emit=emit).install()
    try:
        population = [make_system() for _ in range(2)]
        levels = ParetoLevels(population, population)
        InitialParetoLevelSorting().apply(levels, {})
        # A second call is a no-op in EPDE itself and must be one here too.
        InitialParetoLevelSorting().apply(levels, {})
    finally:
        observer.uninstall()

    generations = collect(events, "generation")
    assert [entry["label"] for entry in generations] == ["initial population"]


def test_crossover_and_mutation_are_recorded_as_ancestry(fake_epde, recorder):
    events, emit = recorder
    observer = EvolutionObserver(multiobjective=True, emit=emit).install()
    try:
        mother, father = make_system(), make_system()
        levels = ParetoLevels([mother, father], [mother])
        InitialParetoLevelSorting().apply(levels, {})

        first, second = ChromosomeCrossover().apply((copy.deepcopy(mother), copy.deepcopy(father)), {})
        SystemMutation().apply(first, {})

        levels.population = [mother, father, first, second]
        levels.levels = [[first]]
        optimizer = MOEADDOptimizer(levels, weights=[0])
        optimizer.set_strategy(None)
        MOEADDSectorProcesser().run(levels, {})
    finally:
        observer.uninstall()

    populations = collect(events, "population")
    assert len(populations) == 2
    latest = {entry["uid"]: entry for entry in populations[-1]["individuals"]}

    offspring = [entry for entry in latest.values() if entry["operators"]]
    assert len(offspring) == 2

    crossed = next(entry for entry in offspring if len(entry["operators"]) == 2)
    assert [operator["type"] for operator in crossed["operators"]] == ["crossover", "mutation"]
    # Two parents on the first link, none on the second: the chain consumes the
    # crossover's own output.
    assert len(crossed["operators"][0]["parents"]) == 2
    assert crossed["operators"][1]["parents"] == []


def test_a_single_objective_generation_is_one_traversal(fake_epde, recorder):
    events, emit = recorder
    observer = EvolutionObserver(multiobjective=False, emit=emit).install()
    try:
        population = [make_system() for _ in range(2)]
        blocks = LinkedBlocks(type("Pop", (), {"population": population})())
        blocks.traversal(None, {})
        blocks.traversal(None, {})
    finally:
        observer.uninstall()

    assert len(collect(events, "generation")) == 2


def test_a_reporting_failure_never_takes_down_the_search(fake_epde, recorder):
    """Progress is a side effect; the search is the job.

    An exception raised while describing a population would otherwise abort a
    run that was working perfectly well.
    """
    events, emit = recorder

    def exploding_emit(kind, **payload):
        if kind == "generation":
            raise RuntimeError("cannot serialise this")
        emit(kind, **payload)

    observer = EvolutionObserver(multiobjective=True, emit=exploding_emit).install()
    try:
        levels = ParetoLevels([make_system()], [])
        MOEADDSectorProcesser().run(levels, {})  # must not raise
    finally:
        observer.uninstall()

    assert any("progress reporting failed" in payload.get("message", "") for _, payload in events)


def test_finish_now_ends_the_search_at_a_generation_boundary(fake_epde, recorder, tmp_path: Path):
    """The counterpart of FEDOT.Web's graceful finish.

    The exception unwinds out of EPDE's own loop with the population intact, so
    the worker still reports a result -- unlike stopping the run, which throws
    the work away.
    """
    events, emit = recorder
    write_controls(tmp_path, {"finish_now": True})
    observer = EvolutionObserver(multiobjective=True, emit=emit, run_dir=tmp_path).install()
    try:
        levels = ParetoLevels([make_system()], [])
        optimizer = MOEADDOptimizer(levels, weights=[0])
        optimizer.set_strategy(None)

        with pytest.raises(FinishRequested):
            MOEADDSectorProcesser().run(levels, {})
    finally:
        observer.uninstall()

    # The generation that triggered it was still reported.
    assert collect(events, "generation")


def test_a_lowered_generation_limit_stops_the_search(fake_epde, recorder, tmp_path: Path):
    """The limit counts rounds of evolution, not reported generations.

    The seed population is reported as a generation and is not a round; adding
    it to the count would end every run one epoch early.
    """
    events, emit = recorder
    observer = EvolutionObserver(multiobjective=True, emit=emit, run_dir=tmp_path).install()
    observer.set_epoch_limit(2)
    try:
        levels = ParetoLevels([make_system()], [])
        optimizer = MOEADDOptimizer(levels, weights=[0])
        optimizer.set_strategy(None)

        InitialParetoLevelSorting().apply(levels, {})  # the seed row
        MOEADDSectorProcesser().run(levels, {})  # first epoch, under the limit
        with pytest.raises(FinishRequested):
            MOEADDSectorProcesser().run(levels, {})  # second epoch reaches it
    finally:
        observer.uninstall()


def test_uninstall_restores_every_patched_method(fake_epde, recorder):
    _, emit = recorder
    original = ChromosomeCrossover.apply

    observer = EvolutionObserver(multiobjective=True, emit=emit).install()
    assert ChromosomeCrossover.apply is not original
    observer.uninstall()

    assert ChromosomeCrossover.apply is original


def test_objective_names_that_do_not_fit_the_vector_fall_back_to_positions(fake_epde, recorder):
    """A confidently wrong axis label is worse than an honest index."""
    events, emit = recorder
    observer = EvolutionObserver(
        multiobjective=True, emit=emit, objective_names=["quality", "complexity", "extra"]
    ).install()
    try:
        levels = ParetoLevels([make_system(objectives=(0.1, 2.0))], [])
        MOEADDSectorProcesser().run(levels, {})
    finally:
        observer.uninstall()

    assert observer.objective_names == ["objective 0", "objective 1"]
    assert any("labelled by position" in payload.get("message", "") for _, payload in events)
