"""Adapters between EPDE and the web layer.

EPDE does not use GOLEM. Everything the FEDOT.Web history view gets for free
from GOLEM -- an ``Individual`` with a uid, recorded parents and the operator
that produced it, a per-generation callback on the optimiser, and an
``OptHistory`` saved at the end -- has no counterpart in EPDE, whose optimisers
work directly on ``SoEq`` objects and keep only the current population. These
modules supply the missing half:

``structures``
    ``SoEq`` / ``Equation`` / ``Term`` / ``Factor`` rendered as the graph,
    text and LaTeX the browser draws. Duck-typed, so it imports nothing from
    EPDE and can be exercised in tests with stand-ins.
``individuals``
    Identity and ancestry. Candidate systems get a uid that survives the
    ``deepcopy`` EPDE uses to breed offspring, which is what makes a genealogy
    recoverable at all.
``observer``
    The per-generation callback EPDE lacks, installed by wrapping the
    optimiser and the handful of operators that create offspring.
``controls``
    Live adjustment of the evolutionary operators while a run is going.
``search``
    Construction of ``EpdeSearch`` from a run configuration, tolerant of the
    signature differences between EPDE releases.
``objectives``
    Pareto bookkeeping: EPDE minimises a vector, not a scalar.

Only ``observer``, ``controls`` and ``search`` need EPDE itself, and they
import it inside functions, so importing this package on a machine without EPDE
is harmless.
"""

from .availability import EpdeAvailability, describe_epde
from .objectives import (
    dominates,
    non_dominated_levels,
    pareto_front_indices,
    summarise_objectives,
)
from .structures import (
    compact_terms,
    describe_system,
    empty_system,
)

__all__ = [
    "EpdeAvailability",
    "compact_terms",
    "describe_epde",
    "describe_system",
    "dominates",
    "empty_system",
    "non_dominated_levels",
    "pareto_front_indices",
    "summarise_objectives",
]
