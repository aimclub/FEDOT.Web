"""End-to-end check that the API can actually drive a FEDOT composition.

This is the integration test the legacy project lacked: it uploads a dataset,
starts a real (very short) AutoML run, follows the progress events and asserts
that a best pipeline comes back in the editor's graph format.
"""

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
def dataset_csv(tmp_path: Path) -> Path:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7)
    size = 400
    x1 = rng.normal(size=size)
    x2 = rng.normal(size=size)
    score = 1.4 * x1 - 0.9 * x2 + rng.normal(scale=0.5, size=size)
    frame = pd.DataFrame({"x1": x1, "x2": x2, "target": (score > 0).astype(int)})

    path = tmp_path / "scoring.csv"
    frame.to_csv(path, index=False)
    return path


def test_run_lifecycle(client: TestClient, dataset_csv: Path) -> None:
    with dataset_csv.open("rb") as handle:
        response = client.post(
            "/api/datasets",
            files={"file": ("scoring.csv", handle, "text/csv")},
            data={"name": "scoring", "task": "classification"},
        )
    assert response.status_code == 201, response.text
    dataset = response.json()
    assert dataset["suggested_target"] == "target"
    assert dataset["n_rows"] == 400
    assert {column["name"] for column in dataset["columns"]} == {"x1", "x2", "target"}

    response = client.post(
        "/api/runs",
        json={
            "name": "smoke",
            "config": {
                "problem": "classification",
                "dataset_uid": dataset["uid"],
                "target": "target",
                "timeout": 0.6,
                "preset": "fast_train",
                "pop_size": 4,
                "num_of_generations": 3,
                "with_tuning": False,
                "cv_folds": 2,
                "n_jobs": 1,
                "seed": 42,
            },
        },
    )
    assert response.status_code == 202, response.text
    run_uid = response.json()["uid"]

    deadline = time.monotonic() + 420
    status = "running"
    while time.monotonic() < deadline:
        status = client.get(f"/api/runs/{run_uid}").json()["status"]
        if status in {"finished", "failed", "cancelled"}:
            break
        time.sleep(2.0)

    progress = client.get(f"/api/runs/{run_uid}/progress").json()
    assert status == "finished", f"run ended as {status}: {progress['run'].get('error')}"

    assert progress["generations"], "no generation events were recorded"
    assert progress["best_pipeline"] is not None
    assert progress["best_pipeline"]["nodes"], "the best pipeline has no nodes"
    assert progress["run"]["metrics"], "no metrics were reported"

    # The best pipeline must be stored and re-loadable as a pipeline record.
    best_uid = progress["run"]["best_pipeline"]
    assert best_uid
    stored = client.get(f"/api/pipelines/{best_uid}")
    assert stored.status_code == 200
    assert stored.json()["graph"]["nodes"]

    # The genealogy must be derivable from the history the worker saved, and every
    # individual in it must resolve to a real pipeline.
    lineage = client.get(f"/api/runs/{run_uid}/lineage")
    assert lineage.status_code == 200, lineage.text
    graph = lineage.json()
    individuals = [node for node in graph["nodes"] if node["kind"] == "individual"]
    assert individuals, "the genealogy has no individuals"

    known_ids = {node["id"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in known_ids and edge["target"] in known_ids

    sample = individuals[-1]
    pipeline = client.get(f"/api/runs/{run_uid}/lineage/{sample['uid']}")
    assert pipeline.status_code == 200, pipeline.text
    assert pipeline.json()["nodes"]
