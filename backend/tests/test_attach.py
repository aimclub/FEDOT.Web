"""Watching a run that was started from a user's own script."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("FEDOTWEB_WORKSPACE", str(tmp_path / "workspace"))
    # A free-ish port, so the test never fights a server the developer is running.
    monkeypatch.setenv("FEDOTWEB_PORT", "8931")

    import fedotweb.settings as settings_module

    settings_module._settings = None  # noqa: SLF001 - reset the cached singleton
    return tmp_path


@pytest.fixture()
def dataset(tmp_path: Path) -> Path:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(19)
    size = 300
    x1, x2 = rng.normal(size=size), rng.normal(size=size)
    frame = pd.DataFrame({"x1": x1, "x2": x2, "target": ((x1 - x2) > 0).astype(int)})
    path = tmp_path / "attached.csv"
    frame.to_csv(path, index=False)
    return path


def test_a_scripted_run_reports_into_the_gui(workspace: Path, dataset: Path) -> None:
    from fedot import Fedot

    from fedotweb import watch
    from fedotweb.settings import get_settings
    from fedotweb.storage.sqlite import Store

    with watch("scripted", open_browser=False, config={"problem": "classification"}) as session:
        run_uid = session.uid
        assert run_uid in session.url

        model = Fedot(
            problem="classification",
            timeout=0.6,
            preset="fast_train",
            seed=3,
            pop_size=4,
            num_of_generations=3,
            with_tuning=False,
            cv_folds=2,
            n_jobs=1,
            optimizer=session.optimizer,
        )
        model.fit(features=str(dataset), target="target")
        session.record_result(model)

    store = Store(get_settings().database_path)
    record = store.get_run(run_uid)
    assert record is not None
    assert record["status"] == "finished"
    assert record["config"]["origin"] == "attached"
    assert record["best_pipeline"], "the fitted pipeline was not stored"

    events = store.list_events(run_uid)
    kinds = {event["kind"] for event in events}
    assert "generation" in kinds, "no progress was reported"
    assert "population" in kinds, "no ancestry was reported"
    assert "finished" in kinds

    # The genealogy must be derivable from what the script reported, exactly as
    # for a run the GUI started itself.
    from fedotweb.history import live_lineage_graph

    graph = live_lineage_graph(events)
    assert graph is not None and graph["nodes"]

    # Fitting without predicting leaves no honest metric, and a made-up one would
    # be worse than none.
    assert record["metrics"] is None


def test_the_server_starts_once_and_is_reused(workspace: Path) -> None:
    from fedotweb.attach import ensure_server

    first = ensure_server()
    second = ensure_server()
    assert first == second

    import urllib.request

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{first}/api/health") as response:
                assert response.status == 200
                return
        except Exception:
            time.sleep(0.5)
    pytest.fail("the attached server never answered")
