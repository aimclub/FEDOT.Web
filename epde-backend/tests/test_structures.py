"""Rendering a candidate system for the browser."""

from __future__ import annotations

from epdeweb.adapters.structures import (
    compact_factor,
    compact_terms,
    describe_system,
)

from .conftest import FakeEquation, FakeFactor, FakeSystem, FakeTerm, make_system


def test_coefficients_shift_past_the_target_term():
    """EPDE stores one weight fewer than there are terms.

    The right-hand side has no coefficient of its own, so every term after it
    reads a weight one position earlier. Getting this wrong produces a plausible
    equation with the wrong numbers rather than an error, which is exactly the
    kind of bug that survives review.
    """
    structure = [
        FakeTerm([FakeFactor("a")]),
        FakeTerm([FakeFactor("b")]),   # target
        FakeTerm([FakeFactor("c")]),
    ]
    equation = FakeEquation(structure, target_idx=1, weights=[1.5, 2.5, 9.0])
    described = describe_system(FakeSystem({"u": equation}))

    terms = described["equations"][0]["terms"]
    assert terms[0]["coefficient"] == 1.5
    assert terms[1]["coefficient"] is None and terms[1]["is_target"]
    assert terms[2]["coefficient"] == 2.5
    assert described["equations"][0]["intercept"] == 9.0


def test_the_master_weight_layout_keeps_the_last_coefficient():
    """Master sizes ``weights_final`` to the coefficients and stores the
    intercept separately, where 1.2.17 appended it.

    Read with the older assumption, master's vector loses its last real
    coefficient and reports it as a constant: ``u_tt = -9.87 u`` becomes
    ``u_tt = -9.87``. That is a well-formed, plausible, entirely wrong equation,
    and nothing anywhere raises -- which is why the layout is decided by length
    rather than by version.
    """
    structure = [
        FakeTerm([FakeFactor("d^2u/dt^2")]),   # target
        FakeTerm([FakeFactor("u")]),
    ]
    equation = FakeEquation(structure, target_idx=0, weights=[-9.87], internal=[-9.87, 0.0])
    described = describe_system(FakeSystem({"u": equation}))["equations"][0]

    assert described["terms"][1]["coefficient"] == -9.87
    assert described["terms"][1]["active"] is True
    assert described["intercept"] == 0.0
    assert described["text"] == "-9.87 * u = d^2u/dt^2"


def test_an_unrecognised_weight_layout_reports_nothing_rather_than_guessing():
    structure = [FakeTerm([FakeFactor("a")]), FakeTerm([FakeFactor("b")])]
    equation = FakeEquation(structure, target_idx=0, weights=[1.0, 2.0, 3.0, 4.0])
    described = describe_system(FakeSystem({"u": equation}))["equations"][0]

    assert described["fitted"] is False
    assert all(term["coefficient"] is None for term in described["terms"])


def test_zero_weight_terms_are_marked_inactive_and_left_out_of_the_text():
    system = make_system(terms=(("d^2u/dx^2", 0.5), ("u", 0.0)))
    described = describe_system(system)
    equation = described["equations"][0]

    assert [term["active"] for term in equation["terms"]] == [True, True, False]
    assert "d^2u/dx^2" in equation["text"]
    assert " u{" not in equation["text"]
    assert equation["text"].endswith("= du/dt")
    assert described["active_terms"] == 2


def test_an_unfitted_equation_still_describes_its_structure():
    """A candidate in mid-run has no weights, and asking for them raises.

    Reporting has to survive that: a generation full of unfitted candidates is
    normal, and losing the whole population event over it would leave the
    genealogy blank exactly when it is most interesting.
    """
    system = make_system(fitted=False)
    described = describe_system(system)
    equation = described["equations"][0]

    assert equation["fitted"] is False
    assert equation["epde_text"] is None
    assert [term["name"] for term in equation["terms"]][0] == "du/dt"


def test_axis_names_replace_epde_positional_ones_zero_based():
    """EPDE numbers derivative axes from zero, not from one.

    On a field laid out (t, x), ``d^2u/dx1^2`` is the second *spatial*
    derivative. Renaming it one-based would call it a time derivative -- still a
    well-formed equation, and the opposite of what was found.
    """
    system = make_system(
        target="d^2u/dx1^2", terms=(("d^2u/dx0^2", 1.0),), objectives=(0.0, 1.0)
    )
    described = describe_system(system, axis_names=["t", "x"])
    equation = described["equations"][0]

    assert equation["terms"][0]["name"] == "d^2u/dx^2"
    assert equation["terms"][1]["name"] == "d^2u/dt^2"
    assert equation["text"] == "1 * d^2u/dt^2 = d^2u/dx^2"


def test_a_factor_keeps_both_its_display_name_and_epdes_own():
    """The renamed label is what a reader sees; EPDE's positional one is kept
    beside it, because that is what the framework's logs and any saved equation
    string will say, and the two have to be matchable."""
    system = make_system(target="d^2u/dx1^2", terms=(("u", 1.0),))
    factor = describe_system(system, axis_names=["t", "x"])["equations"][0]["terms"][0][
        "factors"
    ][0]

    assert factor["label"] == "d^2u/dx^2"
    assert factor["epde_label"] == "d^2u/dx1^2"


def test_a_token_argument_names_its_axis_too():
    factor = FakeFactor("sin", extra={"freq": 3.14, "dim": 1.0})
    assert compact_factor(factor, ["t", "x"]) == "sin(3.14 x)"


def test_compact_factor_folds_parameters_into_a_readable_label():
    plain = FakeFactor("du/dx1")
    powered = FakeFactor("u", power=2.0)
    trig = FakeFactor("sin", extra={"freq": 1.618, "dim": 1.0})

    assert compact_factor(plain) == "du/dx1"
    assert compact_factor(powered) == "u^2"
    assert compact_factor(trig) == "sin(1.62 x1)"


def test_compact_terms_puts_the_right_hand_side_first():
    labels = compact_terms(make_system())
    assert labels[0] == "du/dt"
    assert "d^2u/dx^2" in labels
    # The zero-weight term is not a label worth spending card space on.
    assert "u" not in labels


def test_a_system_of_two_equations_gets_a_root_node():
    equations = {}
    for variable in ("u", "v"):
        equations[variable] = FakeEquation(
            [FakeTerm([FakeFactor(f"d{variable}/dt")]), FakeTerm([FakeFactor(variable)])],
            target_idx=0,
            weights=[0.6, 0.0],
            variable=variable,
        )
    described = describe_system(FakeSystem(equations))

    kinds = [node["kind"] for node in described["nodes"]]
    assert kinds.count("system") == 1
    assert kinds.count("equation") == 2
    assert described["latex"].startswith(r"\begin{cases}")
    assert described["text"].count("\n") == 1
