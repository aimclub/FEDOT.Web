"""Stopping a run must leave it recorded as cancelled, not as a failure."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("FEDOTWEB_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setenv("FEDOTWEB_MAX_CONCURRENT_RUNS", "1")

    import fedotweb.settings as settings_module

    settings_module._settings = None  # noqa: SLF001 - reset the cached singleton

    from fedotweb.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def dataset_uid(client: TestClient, tmp_path: Path) -> str:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(3)
    size = 400
    x1, x2 = rng.normal(size=size), rng.normal(size=size)
    frame = pd.DataFrame({"x1": x1, "x2": x2, "target": ((x1 - x2) > 0).astype(int)})
    path = tmp_path / "cancel.csv"
    frame.to_csv(path, index=False)

    with path.open("rb") as handle:
        response = client.post(
            "/api/datasets",
            files={"file": ("cancel.csv", handle, "text/csv")},
            data={"task": "classification"},
        )
    assert response.status_code == 201, response.text
    return response.json()["uid"]


def test_stopping_a_run_records_it_as_cancelled(client: TestClient, dataset_uid: str) -> None:
    response = client.post(
        "/api/runs",
        json={
            "name": "long",
            "config": {
                "problem": "classification",
                "dataset_uid": dataset_uid,
                "target": "target",
                # Long enough that the run is certainly still going when stopped.
                "timeout": 30,
                "preset": "best_quality",
                "pop_size": 20,
                "num_of_generations": 50,
                "with_tuning": False,
                "cv_folds": 3,
                "n_jobs": 1,
                "seed": 1,
            },
        },
    )
    assert response.status_code == 202, response.text
    run_uid = response.json()["uid"]

    # Wait until composition is genuinely under way before stopping.
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        events = client.get(f"/api/runs/{run_uid}/events").json()
        if any(event["kind"] == "generation" for event in events):
            break
        assert not any(event["kind"] == "error" for event in events), events
        time.sleep(1.5)
    else:
        pytest.fail("the run never reached its first generation")

    # The genealogy must be available *while* the run is going -- that is what
    # makes it usable for monitoring rather than only for post-mortems.
    live = client.get(f"/api/runs/{run_uid}/lineage")
    assert live.status_code == 200, live.text
    graph = live.json()
    assert graph["source"] == "live" and graph["is_live"] is True
    assert graph["nodes"], "the live genealogy is empty"

    known_ids = {node["id"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in known_ids and edge["target"] in known_ids

    # Nothing is final until the run ends; the leader is marked as best so far.
    individuals = [node for node in graph["nodes"] if node["kind"] == "individual"]
    assert not any(node["is_final_choice"] for node in individuals)
    assert any(node["is_current_best"] for node in individuals)

    # And a node in the live graph must open the pipeline it stands for.
    pipeline = client.get(f"/api/runs/{run_uid}/lineage/{individuals[0]['uid']}")
    assert pipeline.status_code == 200, pipeline.text
    assert pipeline.json()["nodes"]

    assert client.post(f"/api/runs/{run_uid}/stop").status_code == 200

    # The tail finalises asynchronously once the worker is gone.
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        record = client.get(f"/api/runs/{run_uid}").json()
        if record["status"] not in {"running", "pending"}:
            break
        time.sleep(1.0)

    assert record["status"] == "cancelled", record
    assert record["error"] is None

    # The concurrency slot must be free again immediately.
    again = client.post(
        "/api/runs",
        json={
            "config": {
                "problem": "classification",
                "dataset_uid": dataset_uid,
                "target": "target",
                "timeout": 0.5,
                "preset": "fast_train",
                "pop_size": 3,
                "num_of_generations": 2,
                "with_tuning": False,
                "cv_folds": 2,
                "n_jobs": 1,
            }
        },
    )
    assert again.status_code == 202, again.text
    client.post(f"/api/runs/{again.json()['uid']}/stop")


def test_stopping_a_finished_run_is_a_conflict(client: TestClient, dataset_uid: str) -> None:
    response = client.post(
        "/api/runs",
        json={
            "config": {
                "problem": "classification",
                "dataset_uid": dataset_uid,
                "target": "target",
                "timeout": 0.5,
                "preset": "fast_train",
                "pop_size": 3,
                "num_of_generations": 2,
                "with_tuning": False,
                "cv_folds": 2,
                "n_jobs": 1,
            }
        },
    )
    run_uid = response.json()["uid"]

    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        if client.get(f"/api/runs/{run_uid}").json()["status"] not in {"running", "pending"}:
            break
        time.sleep(2.0)

    assert client.post(f"/api/runs/{run_uid}/stop").status_code == 409
