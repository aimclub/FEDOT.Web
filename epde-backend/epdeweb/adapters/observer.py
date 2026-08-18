"""The per-generation callback EPDE does not have.

GOLEM offers ``set_iteration_callback``, which is what lets FEDOT.Web draw a
genealogy while a composition is still running. EPDE's optimisers expose no such
hook: ``MOEADDOptimizer.optimize`` runs its epochs to completion and the
single-objective ``EvolutionaryStrategy`` loops until its stop criterion, and
neither offers a place to look in. Nor is there an ``OptHistory`` at the end --
when a run finishes, all that exists is the final population.

So the hook is installed from the outside, by wrapping four things:

``MOEADDSectorProcesser.run``
    called once per weight vector, so counting calls against the number of
    weights recovers the epoch boundary in every EPDE build. Nothing in the
    optimiser needs to change, and no epoch-loop internals are relied on.
``LinkedBlocks.traversal``
    one call is exactly one generation of the single-objective strategy.
``ChromosomeCrossover.apply`` / ``SystemMutation.apply``
    the two points where a new candidate comes into existence. Ancestry is read
    off the inherited record (see :mod:`epdeweb.adapters.individuals`) before it
    is overwritten.
``InitialParetoLevelSorting.apply``
    where the seed population is first placed, so generation zero is the
    population EPDE started from rather than the first one it had already
    changed.

The wrappers are installed on the classes, not on instances: EPDE builds its
operators deep inside a strategy director, and there is no supported way to
reach the objects from outside before the run starts. A worker process runs one
search, so a process-wide patch is exactly scoped, and :meth:`uninstall` puts
the originals back for the tests.

Everything here is written so a failure in reporting can never take down the
search. A raised exception inside a wrapper is caught, reported as a log event
and swallowed; the only exception allowed through is :class:`FinishRequested`,
which is how a graceful mid-run finish is delivered.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import controls as controls_module
from .individuals import CROSSOVER, MUTATION, IndividualRegistry, install_registry
from .objectives import (
    clean_objectives,
    hypervolume_2d,
    non_dominated_levels,
    pareto_front_indices,
    summarise_objectives,
)
from .structures import compact_terms, describe_system

logger = logging.getLogger("epdeweb.observer")

#: Above this population size the per-individual system structure is left out of
#: the population event. The genealogy still draws every node; opening one falls
#: back to rebuilding it from the run's saved history.
MAX_DESCRIBED_INDIVIDUALS = 80


class FinishRequested(Exception):
    """Raised inside the search to end it after the current generation.

    Distinct from stopping the run: the exception unwinds out of ``optimize``
    with the population object intact, so the worker still reports a result.
    """


@dataclass
class _PatchSite:
    owner: Any
    name: str
    original: Any


@dataclass
class GenerationRecord:
    """One reported generation, kept so the run can save its own history."""

    index: int
    label: str
    individuals: list[dict[str, Any]]
    front_uids: list[str]
    elapsed: float


class EvolutionObserver:
    """Watches one EPDE search and reports it generation by generation."""

    def __init__(
        self,
        *,
        multiobjective: bool,
        emit: Callable[..., None],
        objective_names: list[str] | None = None,
        axis_names: list[str] | None = None,
        run_dir: Path | None = None,
        registry: IndividualRegistry | None = None,
    ) -> None:
        self._multiobjective = multiobjective
        self._emit = emit
        self._objective_names = objective_names or []
        #: The dataset's coordinate names, so a derivative reads ``du/dt``
        #: rather than EPDE's positional ``du/dx1``.
        self._axis_names = axis_names or []
        self._run_dir = run_dir
        self.registry = registry or IndividualRegistry()

        self._patches: list[_PatchSite] = []
        self._optimizer: Any = None
        self._operators: dict[str, list[Any]] = {}
        self._sectors = 0
        self._sector_calls = 0
        self._generation = 0
        #: Rounds of evolution completed. Counted separately from reported
        #: generations because the seed population is reported as one and is not
        #: a round -- comparing the two would cut every run one epoch short.
        self._epochs = 0
        self._started = time.monotonic()
        self._reference_point: list[float] | None = None
        self._epoch_limit: int | None = None
        self._deadline: float | None = None
        self._names_checked = False
        self.generations: list[GenerationRecord] = []

    # ------------------------------------------------------------------ install

    def install(self) -> EvolutionObserver:
        install_registry(self.registry)
        _activate(self)

        self._patch("epde.operators.multiobjective.variation", "ChromosomeCrossover", "apply", _crossover_wrapper)
        self._patch("epde.operators.singleobjective.variation", "ChromosomeCrossover", "apply", _crossover_wrapper)
        self._patch("epde.operators.multiobjective.mutations", "SystemMutation", "apply", _mutation_wrapper)
        self._patch("epde.operators.singleobjective.mutations", "SystemMutation", "apply", _mutation_wrapper)

        # ``set_strategy`` is the one call every optimiser makes after it is
        # constructed and before it starts, so it is where the observer gets
        # hold of the object. ``EpdeSearch.fit`` builds the optimiser itself and
        # never hands it out beforehand, so there is no other moment to attach.
        self._patch(
            "epde.optimizers.moeadd.moeadd", "MOEADDOptimizer", "set_strategy", _attach_wrapper
        )
        self._patch(
            "epde.optimizers.single_criterion.optimizer",
            "SimpleOptimizer",
            "set_strategy",
            _attach_wrapper,
        )

        if self._multiobjective:
            self._patch(
                "epde.optimizers.moeadd.strategy_elems",
                "MOEADDSectorProcesser",
                "run",
                _sector_wrapper,
            )
            self._patch(
                "epde.operators.multiobjective.moeadd_specific",
                "InitialParetoLevelSorting",
                "apply",
                _initial_sort_wrapper,
            )
        else:
            self._patch("epde.optimizers.blocks", "LinkedBlocks", "traversal", _traversal_wrapper)
        return self

    def uninstall(self) -> None:
        for site in reversed(self._patches):
            setattr(site.owner, site.name, site.original)
        self._patches.clear()
        _activate(None)
        install_registry(None)

    def _patch(self, module_name: str, class_name: str, method: str, wrapper: Callable) -> None:
        try:
            module = __import__(module_name, fromlist=[class_name])
            owner = getattr(module, class_name)
        except (ImportError, AttributeError):
            # A build without this operator simply reports a little less; the
            # single- and multi-objective operator sets are separate hierarchies
            # and only one of them exists in some builds.
            return
        original = getattr(owner, method, None)
        if original is None or getattr(original, "_epdeweb_wrapped", False):
            return
        wrapped = wrapper(original)
        wrapped._epdeweb_wrapped = True  # type: ignore[attr-defined]
        setattr(owner, method, wrapped)
        self._patches.append(_PatchSite(owner=owner, name=method, original=original))

    # ------------------------------------------------------------------- attach

    def attach(self, optimizer: Any) -> None:
        """Remember the optimiser so populations and operators can be reached."""
        self._optimizer = optimizer
        strategy = getattr(optimizer, "sector_processer", None) or getattr(optimizer, "strategy", None)
        self._operators = controls_module.collect_operators(strategy) if strategy else {}
        weights = getattr(optimizer, "weights", None)
        self._sectors = len(weights) if weights is not None else 0
        self._emit(
            "operators",
            available=sorted(self._operators),
            controls=controls_module.describe_specs(),
            effective=controls_module.describe_effective(self._operators),
        )

    def set_epoch_limit(self, epochs: int | None) -> None:
        self._epoch_limit = epochs

    def set_time_budget(self, minutes: float | None) -> None:
        """Give the run a wall-clock budget.

        EPDE has no time budget of its own -- it runs the epochs it was given,
        however long each takes, and a fit on a large field can spend minutes
        per epoch. The budget is enforced at generation boundaries, so it ends
        the run with a population rather than by killing it.
        """
        self._deadline = None if minutes is None else self._started + float(minutes) * 60.0

    # ----------------------------------------------------------------- capture

    def capture(self, population: list[Any], *, label: str, front: list[Any] | None = None) -> None:
        """Report one generation: summary, ancestry and the leading candidates."""
        members = [system for system in population if system is not None]
        if not members:
            return

        records = self.registry.snapshot(members, self._generation)
        objectives = [clean_objectives(_objectives_of(system)) for system in members]
        ranks = non_dominated_levels(objectives)
        self._check_objective_names(objectives)

        front_uids = self._front_uids(members, records, objectives, front)
        describe_structures = len(members) <= MAX_DESCRIBED_INDIVIDUALS

        individuals: list[dict[str, Any]] = []
        for system, record, values, rank in zip(members, records, objectives, ranks, strict=True):
            entry: dict[str, Any] = {
                "uid": record.uid,
                "objectives": values,
                "pareto_rank": rank,
                "terms": compact_terms(system, axis_names=self._axis_names),
                "born_generation": record.born_generation,
                "operators": [operator.as_dict() for operator in record.operators],
            }
            if describe_structures:
                entry["system"] = describe_system(
                    system,
                    uid=record.uid,
                    objectives=values,
                    objective_names=self._objective_names,
                    generation=self._generation,
                    axis_names=self._axis_names,
                )
            individuals.append(entry)

        summary = summarise_objectives(objectives, self._objective_names)
        summary["hypervolume"] = self._hypervolume(objectives)
        # The optimiser's own front is authoritative where it has one, so it
        # replaces the count `summarise_objectives` derives from the vectors.
        summary["front_size"] = len(front_uids)

        best = self._representative(individuals, front_uids)
        self._emit(
            "generation",
            generation=self._generation,
            label=label,
            elapsed=round(time.monotonic() - self._started, 3),
            objective_names=self._objective_names,
            best=best,
            **summary,
        )
        # Ancestry travels in its own event: it is an order of magnitude larger
        # than the summary, and a client that only wants the objective curves
        # should not have to parse it.
        self._emit(
            "population",
            generation=self._generation,
            label=label,
            individuals=individuals,
            front_uids=front_uids,
        )

        self.generations.append(
            GenerationRecord(
                index=self._generation,
                label=label,
                individuals=individuals,
                front_uids=front_uids,
                elapsed=round(time.monotonic() - self._started, 3),
            )
        )
        self._generation += 1

    def _check_objective_names(self, objectives: list[list[float] | None]) -> None:
        """Make sure the axis labels match the vector they claim to describe.

        The names are predicted from the configuration -- one quality value per
        equation, then one second-axis value per equation -- and that layout has
        held across every EPDE build supported here. If some build lays it out
        differently, a confidently wrong pair of axis labels on a Pareto chart is
        worse than no labels at all, so the prediction is checked against the
        first real vector and dropped if it does not fit.
        """
        if self._names_checked:
            return
        width = next((len(values) for values in objectives if values), None)
        if width is None:
            return
        self._names_checked = True
        if len(self._objective_names) == width:
            return
        self.log(
            f"This EPDE build reports {width} objectives, not the "
            f"{len(self._objective_names)} expected from the configuration; "
            "the Pareto axes are labelled by position.",
            level="warning",
        )
        self._objective_names = [f"objective {index}" for index in range(width)]

    @property
    def objective_names(self) -> list[str]:
        return list(self._objective_names)

    def _front_uids(
        self,
        members: list[Any],
        records: list[Any],
        objectives: list[list[float] | None],
        front: list[Any] | None,
    ) -> list[str]:
        """The uids of the leading candidates.

        EPDE's own non-dominated level 0 is preferred when the optimiser offers
        it, because that is the set the algorithm is actually steering towards;
        recomputing from the objectives is the fallback for the single-objective
        path, where there are no levels.
        """
        if front:
            identity = {id(system): record.uid for system, record in zip(members, records, strict=True)}
            uids = [identity[id(system)] for system in front if id(system) in identity]
            if uids:
                return uids
        return [records[index].uid for index in pareto_front_indices(objectives)]

    def _representative(self, individuals: list[dict[str, Any]], front_uids: list[str]) -> dict[str, Any] | None:
        """One candidate to show as "the current best".

        A multi-objective run has no single best, so the front member with the
        lowest discrepancy is shown and the rest of the front is a click away on
        the Pareto chart. Picking by the first objective rather than by some
        aggregate keeps the choice explainable: it is the most accurate
        equation on the front, whatever its complexity.
        """
        on_front = [entry for entry in individuals if entry["uid"] in set(front_uids)]
        candidates = on_front or individuals
        scored = [entry for entry in candidates if entry.get("objectives")]
        if not scored:
            return None
        best = min(scored, key=lambda entry: entry["objectives"][0])
        return best.get("system") or {"uid": best["uid"], "objectives": best["objectives"]}

    def _hypervolume(self, objectives: list[list[float] | None]) -> float | None:
        """Dominated volume against a reference fixed at the first generation.

        Fixing the reference is the point: a per-generation reference would
        change the scale every time and turn a convergence measure into noise.
        """
        evaluated = [values for values in objectives if values and len(values) >= 2]
        if not evaluated:
            return None
        if self._reference_point is None:
            worst = [max(values[index] for values in evaluated) for index in range(2)]
            # A little headroom, so the first generation itself has non-zero
            # volume and the curve starts somewhere rather than at exactly zero.
            self._reference_point = [value * 1.1 + 1e-9 for value in worst]
        front = [evaluated[index] for index in pareto_front_indices(evaluated)]
        return hypervolume_2d(front, self._reference_point)

    # ---------------------------------------------------------------- callbacks

    def on_sector_run(self, population: Any) -> None:
        """One weight vector processed; an epoch ends when all have been."""
        self._sector_calls += 1
        sectors = self._sectors or 1
        if self._sector_calls % sectors != 0:
            self._emit(
                "progress",
                generation=self._generation,
                sector=self._sector_calls % sectors,
                sectors=sectors,
            )
            return
        self._epochs = self._sector_calls // sectors
        epoch = self._epochs
        self.capture(
            _members(population),
            label=f"gen {epoch}",
            front=_front_of(population),
        )
        self._between_generations()

    def on_traversal(self, population: Any) -> None:
        """One generation of the single-objective strategy."""
        self._epochs += 1
        self.capture(_members(population), label=f"gen {self._epochs}")
        self._between_generations()

    def on_initial_population(self, population: Any) -> None:
        if self._generation == 0:
            self.capture(
                _members(population),
                label="initial population",
                front=_front_of(population),
            )

    def capture_initial(self, population: Any) -> None:
        """Report the seed population of a single-objective run.

        The multi-objective path gets this from ``InitialParetoLevelSorting``,
        which is where MOEA/D first places its candidates. The simple optimiser
        builds its population in ``__init__``, so the worker calls this instead.
        """
        self.on_initial_population(population)

    def _between_generations(self) -> None:
        """Apply pending control requests, and honour a finish request."""
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise FinishRequested("The time budget for this run has run out")
        if self._run_dir is None:
            return
        try:
            requested = controls_module.read_controls(self._run_dir)
            changes = controls_module.apply_controls(self._operators, requested)
            if changes:
                self._emit("control_applied", generation=self._generation, changes=changes)
            self._emit(
                "effective_params",
                generation=self._generation,
                effective=controls_module.describe_effective(self._operators),
                epoch_limit=requested.epochs if requested.epochs is not None else self._epoch_limit,
            )
        except FinishRequested:
            raise
        except Exception as exc:  # noqa: BLE001
            self._emit("log", level="warning", message=f"controls could not be applied: {exc}")
            return

        limit = requested.epochs if requested.epochs is not None else self._epoch_limit
        if requested.finish_now:
            raise FinishRequested("The run was asked to finish after this generation")
        if limit is not None and self._epochs >= limit:
            raise FinishRequested(f"The generation limit was reached at {limit}")

    def log(self, message: str, level: str = "info") -> None:
        self._emit("log", level=level, message=message)


# --------------------------------------------------------------- module state

_observer: EvolutionObserver | None = None


def _activate(observer: EvolutionObserver | None) -> None:
    global _observer
    _observer = observer


def current_observer() -> EvolutionObserver | None:
    return _observer


def _guard(action: Callable[[EvolutionObserver], None]) -> None:
    """Run a reporting step; never let it break the search.

    ``FinishRequested`` is deliberately re-raised: it is not a failure but the
    mechanism by which a mid-run finish is delivered.
    """
    observer = _observer
    if observer is None:
        return
    try:
        action(observer)
    except FinishRequested:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("progress reporting failed: %s", exc, exc_info=True)
        try:
            observer.log(f"progress reporting failed: {exc}", level="warning")
        except Exception:  # noqa: BLE001
            pass


# -------------------------------------------------------------------- wrappers


def _crossover_wrapper(original: Callable) -> Callable:
    def apply(self, objective, arguments):  # noqa: ANN001 - mirrors EPDE's signature
        parents: list[str] = []
        registry = _observer.registry if _observer is not None else None
        if registry is not None:
            try:
                parents = [registry.uid_of(parent) for parent in objective]
            except Exception:  # noqa: BLE001
                parents = []

        result = original(self, objective, arguments)

        if registry is not None and parents:

            def record(observer: EvolutionObserver) -> None:
                for child in _as_tuple(result):
                    observer.registry.record_offspring(
                        child, parents=parents, operator_type=CROSSOVER, label="crossover"
                    )

            _guard(record)
        return result

    return apply


def _mutation_wrapper(original: Callable) -> Callable:
    def apply(self, objective, arguments):  # noqa: ANN001 - mirrors EPDE's signature
        registry = _observer.registry if _observer is not None else None
        parent = registry.uid_of(objective) if registry is not None else None

        result = original(self, objective, arguments)

        if registry is not None and parent:
            # Some builds mutate in place and return the same object; others
            # deepcopy first. Either way the offspring is what came back, and
            # recording it against the uid read *before* the call is what makes
            # both cases produce the same edge.
            offspring = result if result is not None else objective

            def record(observer: EvolutionObserver) -> None:
                observer.registry.record_offspring(
                    offspring, parents=[parent], operator_type=MUTATION, label="mutation"
                )

            _guard(record)
        return result

    return apply


def _sector_wrapper(original: Callable) -> Callable:
    def run(self, population_subset, EA_kwargs):  # noqa: ANN001, N803 - mirrors EPDE
        result = original(self, population_subset, EA_kwargs)
        _guard(lambda observer: observer.on_sector_run(population_subset))
        return result

    return run


def _traversal_wrapper(original: Callable) -> Callable:
    def traversal(self, input_obj, EA_kwargs):  # noqa: ANN001, N803 - mirrors EPDE
        result = original(self, input_obj, EA_kwargs)
        _guard(lambda observer: observer.on_traversal(_output_of(self, input_obj)))
        return result

    return traversal


def _attach_wrapper(original: Callable) -> Callable:
    def set_strategy(self, strategy_director):  # noqa: ANN001 - mirrors EPDE
        result = original(self, strategy_director)
        _guard(lambda observer: observer.attach(self))
        return result

    return set_strategy


def _initial_sort_wrapper(original: Callable) -> Callable:
    def apply(self, objective, arguments):  # noqa: ANN001 - mirrors EPDE's signature
        result = original(self, objective, arguments)
        _guard(lambda observer: observer.on_initial_population(objective))
        return result

    return apply


# ------------------------------------------------------------------- utilities


def _as_tuple(value: Any) -> tuple[Any, ...]:
    if isinstance(value, tuple):
        return value
    return (value,) if value is not None else ()


def _members(population: Any) -> list[Any]:
    """The candidate systems inside whatever the optimiser handed us.

    ``ParetoLevels`` (multi-objective) and ``Population`` (single-objective) both
    keep the flat list on ``.population``; a bare list is what the tests pass.
    """
    if population is None:
        return []
    inner = getattr(population, "population", None)
    if isinstance(inner, list):
        return list(inner)
    if isinstance(population, list):
        return list(population)
    try:
        return list(population)
    except TypeError:
        return []


def _front_of(population: Any) -> list[Any] | None:
    levels = getattr(population, "levels", None)
    if isinstance(levels, list) and levels:
        first = levels[0]
        if isinstance(first, list):
            return list(first)
    return None


def _output_of(blocks: Any, fallback: Any) -> Any:
    try:
        return blocks.output
    except Exception:  # noqa: BLE001 - the strategy had no terminal block yet
        return fallback


def _objectives_of(system: Any) -> list[float] | None:
    try:
        values = system.obj_fun
    except Exception:  # noqa: BLE001 - fitness not computed for this candidate
        return None
    try:
        return [float(value) for value in values]
    except (TypeError, ValueError):
        return None
