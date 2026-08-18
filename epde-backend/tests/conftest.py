"""Stand-ins for EPDE's own objects.

The adapters are duck-typed on purpose, so the whole reporting path -- identity,
ancestry, the rendered equation, the genealogy -- can be exercised without
installing EPDE, torch and scikit-learn to run a test. These fakes mirror the
attributes the adapters actually read, and only those.
"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest


class FakeFactor:
    """Mirrors ``epde.structure.factor.Factor``."""

    def __init__(self, label, *, power=1.0, family="u", variable="u", is_deriv=False,
                 deriv_code=None, extra=None):
        self.label = label
        self.ftype = family
        self.variable = variable
        self.is_deriv = is_deriv
        self.deriv_code = deriv_code
        values = [power] + list((extra or {}).values())
        self.params = np.array(values, dtype=float)
        description = {0: {"name": "power"}}
        for index, name in enumerate((extra or {}), start=1):
            description[index] = {"name": name}
        self.params_description = description

    @property
    def name(self):
        return f"{self.label}{{power: {self.params[0]}}}"

    @property
    def latex_name(self):
        return rf"\mathrm{{{self.label}}}"


class FakeTerm:
    def __init__(self, factors):
        self.structure = list(factors)

    @property
    def name(self):
        return " * ".join(factor.name for factor in self.structure)


class FakeEquation:
    """Mirrors the parts of ``epde.structure.main_structures.Equation`` that are read."""

    def __init__(self, terms, *, target_idx=0, weights=None, variable="u", fitness=0.5,
                 internal=None):
        self.structure = list(terms)
        self.target_idx = target_idx
        self.main_var_to_explain = variable
        self.metaparameters = {("sparsity", variable): {"optimizable": True, "value": 0.01}}
        self._fitness_value = fitness
        self.weights_final_evald = weights is not None
        self._weights = list(weights) if weights is not None else None
        # EPDE master keeps the intercept here instead of appending it to
        # ``weights_final``; both layouts have to be readable.
        self.weights_internal_evald = internal is not None
        self._internal = list(internal) if internal is not None else None

    @property
    def weights_final(self):
        if not self.weights_final_evald:
            raise AttributeError("Final weights called before initialization")
        return self._weights

    @property
    def weights_internal(self):
        if not self.weights_internal_evald:
            raise AttributeError("Internal weights called before initialization")
        return self._internal

    @property
    def fitness_value(self):
        return self._fitness_value

    @property
    def text_form(self):
        if not self.weights_final_evald:
            raise AttributeError("not fitted")
        return "epde text form"


class FakeChromosome:
    def __init__(self, equations):
        self._equations = dict(equations)
        self.equation_keys = list(self._equations)

    def __getitem__(self, key):
        return self._equations[key]


class FakeSystem:
    """Mirrors ``epde.structure.main_structures.SoEq``.

    The important property is the one the ancestry mechanism rests on: a copy
    carries the attributes of its original, because EPDE breeds by deepcopy.
    """

    def __init__(self, equations, objectives=None):
        self.vals = FakeChromosome(equations)
        self.vars_to_describe = list(equations)
        self._objectives = objectives

    @property
    def obj_fun(self):
        if self._objectives is None:
            raise AttributeError("fitness not computed")
        return np.array(self._objectives, dtype=float)

    def __deepcopy__(self, memo=None):
        clone = FakeSystem.__new__(FakeSystem)
        memo = memo if memo is not None else {}
        memo[id(self)] = clone
        for key, value in self.__dict__.items():
            setattr(clone, key, copy.deepcopy(value, memo))
        return clone


def make_system(*, target="du/dt", terms=(("d^2u/dx^2", 0.5), ("u", 0.0)), objectives=(0.1, 3.0),
                variable="u", fitted=True):
    """A one-equation system whose right-hand side is ``target``."""
    structure = [FakeTerm([FakeFactor(target, is_deriv=True, deriv_code=[0], variable=variable)])]
    weights = []
    for label, coefficient in terms:
        structure.append(FakeTerm([FakeFactor(label, is_deriv="/" in label, variable=variable)]))
        weights.append(coefficient)
    weights.append(0.0)  # intercept
    equation = FakeEquation(
        structure, target_idx=0, weights=weights if fitted else None, variable=variable
    )
    return FakeSystem({variable: equation}, objectives=list(objectives) if objectives else None)


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An isolated workspace, so tests never touch the user's real one."""
    monkeypatch.setenv("EPDEWEB_WORKSPACE", str(tmp_path))
    import epdeweb.settings as settings_module

    settings_module._settings = None
    yield tmp_path
    settings_module._settings = None


@pytest.fixture()
def client(workspace: Path):
    from fastapi.testclient import TestClient

    from epdeweb.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
