"""What a discovered equation rests on."""

from __future__ import annotations

import numpy as np

from epdeweb.adapters.ablation import equation_ablation, system_ablation

from .conftest import FakeEquation, FakeFactor, FakeSystem, FakeTerm


class EvaluableEquation(FakeEquation):
    """A fitted equation that can hand back its design matrix, as EPDE's does."""

    def __init__(self, target, columns, coefficients, intercept, *, three_tuple=True):
        structure = [FakeTerm([FakeFactor("target")])] + [
            FakeTerm([FakeFactor(f"term{index}")]) for index in range(len(coefficients))
        ]
        super().__init__(
            structure,
            target_idx=0,
            weights=list(coefficients),
            internal=list(coefficients) + [intercept],
        )
        self._target = np.asarray(target, dtype=float)
        self._columns = np.asarray(columns, dtype=float)
        self._three_tuple = three_tuple

    def evaluate(self, normalize=True, return_val=False, grids=None):
        if self._three_tuple:
            # EPDE master returns (value, target, features).
            return None, self._target, self._columns
        # Earlier releases returned (target, features).
        return self._target, self._columns


def build(coefficients=(2.0,), intercept=0.0, **kwargs):
    grid = np.linspace(0.0, 1.0, 50)
    columns = np.stack([grid, np.ones_like(grid)][: len(coefficients)], axis=1)
    target = columns @ np.asarray(coefficients, dtype=float) + intercept
    return EvaluableEquation(target, columns, coefficients, intercept, **kwargs)


def test_removing_the_term_the_equation_rests_on_blows_up_the_residual():
    report = equation_ablation(build(coefficients=(2.0,)))

    assert report["error"] is None
    assert report["relative_residual"] < 1e-9
    entry = report["terms"][0]
    # The fit is exact, so dropping its only term leaves the whole signal in
    # the residual: without it the equation explains nothing.
    assert entry["residual_without"] > 0.99
    assert entry["magnitude"] > 0.5


def test_a_term_carrying_nothing_leaves_the_residual_where_it_was():
    grid = np.linspace(0.0, 1.0, 50)
    columns = np.stack([grid, np.sin(grid)], axis=1)
    # An imperfect fit, so the baseline residual is non-zero and the growth
    # factor is defined -- which is the ordinary case for real data.
    target = 2.0 * grid + 0.05 * np.cos(7.0 * grid)
    equation = EvaluableEquation(target, columns, (2.0, 0.0), 0.0)

    report = equation_ablation(equation)
    dead = next(entry for entry in report["terms"] if entry["coefficient"] == 0.0)
    live = next(entry for entry in report["terms"] if entry["coefficient"] != 0.0)

    assert dead["residual_ratio"] == 1.0
    assert dead["residual_without"] == report["relative_residual"]
    assert dead["active"] is False
    assert live["residual_ratio"] > 1.0


def test_both_return_shapes_of_evaluate_are_understood():
    """Master returns ``(value, target, features)``; 1.2.17 returned two.

    Unpacking positionally against the wrong one puts the features matrix where
    the target belongs, which produces plausible nonsense rather than an error.
    """
    modern = equation_ablation(build(three_tuple=True))
    legacy = equation_ablation(build(three_tuple=False))

    assert modern["error"] is None and legacy["error"] is None
    assert modern["terms"][0]["residual_without"] == legacy["terms"][0]["residual_without"]


def test_an_unfitted_equation_reports_why_rather_than_nothing():
    equation = FakeEquation([FakeTerm([FakeFactor("a")])], target_idx=0, weights=None)
    report = equation_ablation(equation)

    assert report["error"] and "never fitted" in report["error"]
    assert report["terms"] == []


def test_a_mismatched_design_matrix_is_refused_rather_than_guessed():
    equation = build(coefficients=(2.0,))
    # One more coefficient than the matrix has columns: the layout is not the
    # one this adapter knows, so attributing terms would be a guess.
    equation._weights = [2.0, 3.0]
    equation._internal = [2.0, 3.0, 0.0]
    equation.structure.append(FakeTerm([FakeFactor("extra")]))

    report = equation_ablation(equation)
    assert report["error"] is not None
    assert report["terms"] == []


def test_a_system_reports_one_entry_per_equation_keyed_by_the_chromosome():
    """The key says which equation this is; the equation's own recorded
    variable is only a hint and can lag a structural mutation."""
    equations = {"u": build(), "v": build()}
    system = FakeSystem(equations)
    reports = system_ablation(system)

    assert [report["variable"] for report in reports] == ["u", "v"]
