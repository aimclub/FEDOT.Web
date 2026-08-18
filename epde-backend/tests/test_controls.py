"""Steering a search while it runs."""

from __future__ import annotations

from pathlib import Path

from epdeweb.adapters.controls import (
    apply_controls,
    collect_operators,
    describe_effective,
    read_controls,
    write_controls,
)


class FakeOperator:
    """Mirrors ``epde.operators.utils.template.CompoundOperator``."""

    def __init__(self, key, params, suboperators=()):
        self.key = key
        self.params = dict(params)
        self._children = list(suboperators)

    @property
    def suboperators(self):
        return self._children


class FakeBlock:
    def __init__(self, operator):
        self._operator = operator


class FakeStrategy:
    def __init__(self, blocks):
        self.linked_blocks = type("Blocks", (), {"blocks_labeled": blocks})()


def build_strategy():
    term_crossover = FakeOperator("TermCrossover", {"crossover_probability": 0.3})
    chromosome = FakeOperator("ChromosomeCrossover", {}, [term_crossover])
    mutation = FakeOperator("SystemMutation", {"indiv_mutation_prob": 1.0})
    return FakeStrategy({"variation": FakeBlock(chromosome), "mutation": FakeBlock(mutation)})


def test_operators_are_found_through_their_suboperators():
    """The parameters that matter live several levels inside the strategy.

    Writing to the top-level operator would change nothing: the value an
    application reads belongs to the leaf that reads it.
    """
    found = collect_operators(build_strategy())
    assert set(found) == {"ChromosomeCrossover", "TermCrossover", "SystemMutation"}


def test_applying_a_control_writes_into_the_live_operator():
    strategy = build_strategy()
    operators = collect_operators(strategy)
    controls = read_controls(Path("/nonexistent"))
    controls.values["crossover_prob"] = 0.75

    changes = apply_controls(operators, controls)

    assert operators["TermCrossover"][0].params["crossover_probability"] == 0.75
    assert changes and "0.75" in changes[0]


def test_reapplying_the_same_value_reports_no_change():
    """The GUI shows what was actually honoured; repeating a value did nothing."""
    operators = collect_operators(build_strategy())
    controls = read_controls(Path("/nonexistent"))
    controls.values["crossover_prob"] = 0.3  # already the default

    assert apply_controls(operators, controls) == []


def test_a_control_this_build_does_not_have_lands_nowhere_and_says_so():
    """``term_addition_prob`` exists only in some EPDE builds.

    Silently accepting it would leave the GUI showing a setting the search never
    saw, which is worse than showing that nothing changed.
    """
    operators = collect_operators(build_strategy())
    controls = read_controls(Path("/nonexistent"))
    controls.values["term_addition_prob"] = 0.9

    assert apply_controls(operators, controls) == []


def test_effective_values_are_read_back_from_the_operators():
    effective = describe_effective(collect_operators(build_strategy()))

    assert effective["crossover_prob"] == 0.3
    assert effective["mutation_prob"] == 1.0
    assert effective["parents_fraction"] is None


def test_the_request_file_merges_patches_and_clamps_to_range(tmp_path: Path):
    write_controls(tmp_path, {"crossover_prob": 0.5})
    write_controls(tmp_path, {"mutation_prob": 5.0, "finish_now": True})

    controls = read_controls(tmp_path)

    assert controls.values["crossover_prob"] == 0.5   # kept from the first patch
    assert controls.values["mutation_prob"] == 1.0    # clamped to the maximum
    assert controls.finish_now is True


def test_an_unreadable_request_file_is_ignored_rather_than_fatal(tmp_path: Path):
    """The worker reads this file between generations while the API writes it.

    A half-written file is momentary; treating it as an error would end a run
    over a race that resolves itself on the next read.
    """
    (tmp_path / "controls.json").write_text("{ not json", encoding="utf-8")
    controls = read_controls(tmp_path)

    assert controls.values == {} and controls.finish_now is False
