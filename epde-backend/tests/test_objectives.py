"""Pareto bookkeeping: EPDE minimises a vector, not a number."""

from __future__ import annotations

from epdeweb.adapters.objectives import (
    clean_objectives,
    dominates,
    hypervolume_2d,
    non_dominated_levels,
    pareto_front_indices,
    summarise_objectives,
)


def test_domination_needs_to_be_at_least_as_good_everywhere():
    assert dominates([1.0, 1.0], [2.0, 2.0])
    assert dominates([1.0, 2.0], [1.0, 3.0])
    assert not dominates([1.0, 3.0], [2.0, 2.0])  # better on one, worse on the other
    assert not dominates([1.0, 1.0], [1.0, 1.0])  # equal dominates nothing


def test_levels_peel_the_population_front_by_front():
    population = [
        [1.0, 5.0],   # front
        [5.0, 1.0],   # front
        [2.0, 6.0],   # dominated by the first
        [9.0, 9.0],   # dominated by everything
    ]
    assert non_dominated_levels(population) == [0, 0, 1, 2]
    assert pareto_front_indices(population) == [0, 1]


def test_an_unevaluated_candidate_has_no_level_and_never_dominates():
    """A failed evaluation is not a very bad candidate.

    Coercing ``inf`` or ``nan`` into a number would put it on the far end of
    every colour scale and let it sit in the population as if it were real.
    """
    assert clean_objectives([float("nan"), 1.0]) is None
    assert clean_objectives([float("inf"), 1.0]) is None
    assert clean_objectives(["not a number"]) is None
    assert clean_objectives([1, 2]) == [1.0, 2.0]

    levels = non_dominated_levels([[1.0, 1.0], None, [2.0, 2.0]])
    assert levels == [0, None, 1]


def test_the_summary_is_per_objective_rather_than_aggregated():
    """The two axes pull against each other; an average over them hides the
    trade-off the run is exploring."""
    summary = summarise_objectives([[1.0, 5.0], [3.0, 1.0], None], ["quality", "complexity"])

    assert summary["size"] == 3 and summary["evaluated"] == 2
    assert [entry["name"] for entry in summary["objectives"]] == ["quality", "complexity"]
    assert summary["objectives"][0]["best"] == 1.0
    assert summary["objectives"][1]["best"] == 1.0
    assert summary["front_size"] == 2


def test_hypervolume_grows_as_the_front_advances():
    reference = [10.0, 10.0]
    early = hypervolume_2d([[8.0, 8.0]], reference)
    later = hypervolume_2d([[2.0, 8.0], [8.0, 2.0]], reference)

    assert early is not None and later is not None
    assert later > early


def test_a_front_outside_the_reference_contributes_nothing():
    assert hypervolume_2d([[11.0, 11.0]], [10.0, 10.0]) is None
    assert hypervolume_2d([], [10.0, 10.0]) is None
