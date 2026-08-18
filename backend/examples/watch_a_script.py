"""Run FEDOT from your own script and watch it in the browser.

Two ways to do it. The first is one import::

    python examples/watch_a_script.py

The second is explicit, for when you want to name the run::

    python examples/watch_a_script.py --explicit
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


def make_dataset(path: Path) -> Path:
    """A small separable classification problem, so the example runs quickly."""
    rng = np.random.default_rng(11)
    size = 600
    x1, x2 = rng.normal(size=size), rng.normal(size=size)
    score = 1.4 * x1 - 0.9 * x2 + rng.normal(scale=0.5, size=size)
    frame = pd.DataFrame({"x1": x1, "x2": x2, "target": (score > 0).astype(int)})
    frame.to_csv(path, index=False)
    return path


def automatic(data: Path) -> None:
    """The GUI opens by itself; the script is otherwise ordinary FEDOT."""
    from fedot import Fedot

    import fedotweb.autowatch  # noqa: F401  -- the import is the whole integration

    model = Fedot(problem="classification", timeout=5, preset="best_quality", seed=1)
    model.fit(features=str(data), target="target")
    print("done:", model.current_pipeline)


def explicit(data: Path) -> None:
    """The same thing, with the session in hand."""
    from fedot import Fedot

    from fedotweb import watch

    with watch("scoring from a script") as session:
        model = Fedot(
            problem="classification",
            timeout=5,
            preset="best_quality",
            seed=1,
            optimizer=session.optimizer,
        )
        model.fit(features=str(data), target="target")
        session.record_result(model)
        print("done:", model.current_pipeline)


if __name__ == "__main__":
    dataset = make_dataset(Path(__file__).with_name("example_scoring.csv"))
    if "--explicit" in sys.argv:
        explicit(dataset)
    else:
        automatic(dataset)
