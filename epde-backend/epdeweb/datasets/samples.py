"""Built-in fields with a known governing equation.

A discovery framework is hard to evaluate on data whose answer nobody knows, so
the module ships four fields whose equations are exact. They make the GUI usable
on a fresh install without hunting for data, and they make it possible to say
whether a run worked: the expected equation is stated alongside each one, and
the run screen shows it next to what was found.

All four are analytic (the Lotka-Volterra system is integrated with a fixed-step
RK4, which for these parameters tracks the true trajectory far below the noise a
derivative estimate would add), so they are generated on demand rather than
shipped as files.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from .fields import FieldDataset


@dataclass(frozen=True)
class Sample:
    """A synthetic field, and the equation it satisfies."""

    id: str
    name: str
    description: str
    #: The equation the search should recover, in the notation the results use.
    expected: str
    expected_latex: str
    variables: list[str]
    #: Suggested run settings, so the configuration screen starts somewhere sane.
    suggestion: dict[str, Any]
    build: Callable[[], FieldDataset]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "expected": self.expected,
            "expected_latex": self.expected_latex,
            "variables": list(self.variables),
            "suggestion": dict(self.suggestion),
        }


def _wave() -> FieldDataset:
    """u = sin(pi x) cos(pi t), an exact solution of u_tt = u_xx."""
    t = np.linspace(0.0, 1.0, 81)
    x = np.linspace(0.0, 1.0, 81)
    grid_t, grid_x = np.meshgrid(t, x, indexing="ij")
    u = np.sin(np.pi * grid_x) * np.cos(np.pi * grid_t)
    return FieldDataset(variables={"u": u}, axes=[t, x], axis_names=["t", "x"], note="wave equation")


def _heat() -> FieldDataset:
    """u = exp(-pi^2 t) sin(pi x), an exact solution of u_t = u_xx."""
    t = np.linspace(0.0, 0.1, 61)
    x = np.linspace(0.0, 1.0, 81)
    grid_t, grid_x = np.meshgrid(t, x, indexing="ij")
    u = np.exp(-(np.pi**2) * grid_t) * np.sin(np.pi * grid_x)
    return FieldDataset(variables={"u": u}, axes=[t, x], axis_names=["t", "x"], note="heat equation")


def _transport() -> FieldDataset:
    """A Gaussian pulse travelling at speed 1: u_t + u_x = 0."""
    t = np.linspace(0.0, 0.5, 81)
    x = np.linspace(0.0, 2.0, 121)
    grid_t, grid_x = np.meshgrid(t, x, indexing="ij")
    u = np.exp(-(((grid_x - grid_t - 0.5) / 0.15) ** 2))
    return FieldDataset(
        variables={"u": u}, axes=[t, x], axis_names=["t", "x"], note="transport equation"
    )


def _lotka_volterra() -> FieldDataset:
    """Predator and prey populations: du/dt = a u - b u v, dv/dt = -c v + d u v.

    Integrated with fixed-step RK4 rather than an adaptive solver on purpose: an
    evenly spaced sample is what the derivative preprocessors assume, and a
    resampled adaptive trajectory would carry interpolation error into exactly
    the quantity the search is trying to recover.
    """
    alpha, beta, gamma, delta = 0.6, 0.8, 0.9, 0.5
    steps = 601
    t = np.linspace(0.0, 30.0, steps)
    dt = float(t[1] - t[0])

    def derivative(state: np.ndarray) -> np.ndarray:
        prey, predator = state
        return np.array(
            [
                alpha * prey - beta * prey * predator,
                -gamma * predator + delta * prey * predator,
            ]
        )

    trajectory = np.zeros((steps, 2), dtype=float)
    trajectory[0] = np.array([2.0, 1.0])
    for index in range(1, steps):
        state = trajectory[index - 1]
        k1 = derivative(state)
        k2 = derivative(state + 0.5 * dt * k1)
        k3 = derivative(state + 0.5 * dt * k2)
        k4 = derivative(state + dt * k3)
        trajectory[index] = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    return FieldDataset(
        variables={"u": trajectory[:, 0], "v": trajectory[:, 1]},
        axes=[t],
        axis_names=["t"],
        note="Lotka-Volterra system",
    )


SAMPLES: tuple[Sample, ...] = (
    Sample(
        id="wave_1d",
        name="Wave equation (1D)",
        description=(
            "A standing wave on a unit interval, sampled on an 81x81 grid in time and space."
        ),
        expected="d^2u/dt^2 = d^2u/dx^2",
        expected_latex=r"\frac{\partial^2 u}{\partial t^2} = \frac{\partial^2 u}{\partial x^2}",
        variables=["u"],
        suggestion={
            "max_deriv_order": [2, 2],
            "equation_terms_max_number": 5,
            "equation_factors_max_number": 1,
            "boundary": 10,
            "population_size": 8,
            "epochs": 15,
            "token_families": [],
        },
        build=_wave,
    ),
    Sample(
        id="heat_1d",
        name="Heat equation (1D)",
        description="A decaying temperature profile; the simplest non-trivial parabolic case.",
        expected="du/dt = d^2u/dx^2",
        expected_latex=r"\frac{\partial u}{\partial t} = \frac{\partial^2 u}{\partial x^2}",
        variables=["u"],
        suggestion={
            "max_deriv_order": [1, 2],
            "equation_terms_max_number": 4,
            "equation_factors_max_number": 1,
            "boundary": 6,
            "population_size": 8,
            "epochs": 12,
            "token_families": [],
        },
        build=_heat,
    ),
    Sample(
        id="transport_1d",
        name="Transport equation (1D)",
        description="A Gaussian pulse moving at unit speed; first order in both coordinates.",
        expected="du/dt = -du/dx",
        expected_latex=r"\frac{\partial u}{\partial t} = -\frac{\partial u}{\partial x}",
        variables=["u"],
        suggestion={
            "max_deriv_order": [1, 1],
            "equation_terms_max_number": 4,
            "equation_factors_max_number": 1,
            "boundary": 8,
            "population_size": 8,
            "epochs": 12,
            "token_families": [],
        },
        build=_transport,
    ),
    Sample(
        id="lotka_volterra",
        name="Lotka-Volterra system (ODE)",
        description=(
            "Two coupled populations over 30 time units. A system of two equations, "
            "so the search has to discover both at once and the terms are products."
        ),
        expected="du/dt = 0.6 u - 0.8 u v;  dv/dt = -0.9 v + 0.5 u v",
        expected_latex=(
            r"\begin{cases}\frac{du}{dt} = 0.6\,u - 0.8\,uv \\ "
            r"\frac{dv}{dt} = -0.9\,v + 0.5\,uv\end{cases}"
        ),
        variables=["u", "v"],
        suggestion={
            "max_deriv_order": 1,
            "equation_terms_max_number": 4,
            # Products such as u*v are the whole point here, so terms must be
            # allowed more than one factor.
            "equation_factors_max_number": 2,
            "boundary": 10,
            "population_size": 8,
            "epochs": 20,
            "token_families": [],
        },
        build=_lotka_volterra,
    ),
)

SAMPLE_BY_ID = {sample.id: sample for sample in SAMPLES}


def build_sample(sample_id: str) -> tuple[Sample, FieldDataset]:
    sample = SAMPLE_BY_ID.get(sample_id)
    if sample is None:
        raise KeyError(f"Unknown sample: {sample_id}")
    return sample, sample.build()
