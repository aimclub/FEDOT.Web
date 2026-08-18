"""The analyses you ask for: where a score came from, and what it rests on."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("FEDOTWEB_WORKSPACE", str(tmp_path / "workspace"))

    import fedotweb.settings as settings_module

    settings_module._settings = None  # noqa: SLF001 - reset the cached singleton

    from fedotweb.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def dataset_uid(client: TestClient, tmp_path: Path) -> str:
    """A table with a deliberately awkward column, to give preprocessing work."""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(5)
    size = 300
    frame = pd.DataFrame(
        {
            "x1": rng.normal(size=size),
            # Few distinct integers: FEDOT should read this as a category.
            "few_values": rng.integers(0, 3, size=size),
            # One repeated value carries nothing.
            "constant": np.ones(size),
            "target": rng.integers(0, 2, size=size),
        }
    )
    frame.loc[frame.index[:10], "x1"] = np.nan

    path = tmp_path / "messy.csv"
    frame.to_csv(path, index=False)

    with path.open("rb") as handle:
        response = client.post(
            "/api/datasets",
            files={"file": ("messy.csv", handle, "text/csv")},
            data={"task": "classification", "target": "target"},
        )
    assert response.status_code == 201, response.text
    return response.json()["uid"]


@pytest.fixture()
def finished_run(client: TestClient, dataset_uid: str) -> str:
    response = client.post(
        "/api/runs",
        json={
            "name": "for analysis",
            "config": {
                "problem": "classification",
                "dataset_uid": dataset_uid,
                "target": "target",
                "timeout": 0.6,
                "preset": "fast_train",
                "pop_size": 3,
                "num_of_generations": 2,
                "with_tuning": False,
                "cv_folds": 3,
                "n_jobs": 1,
                "seed": 4,
                "metric": "roc_auc",
            },
        },
    )
    assert response.status_code == 202, response.text
    run_uid = response.json()["uid"]

    deadline = time.monotonic() + 420
    while time.monotonic() < deadline:
        record = client.get(f"/api/runs/{run_uid}").json()
        if record["status"] not in {"running", "pending"}:
            break
        time.sleep(2.0)
    assert record["status"] == "finished", record.get("error")
    assert record["best_pipeline"]
    return run_uid


def await_analysis(client: TestClient, analysis_uid: str, deadline: float = 900) -> dict:
    end = time.monotonic() + deadline
    while time.monotonic() < end:
        record = client.get(f"/api/analyses/{analysis_uid}").json()
        if record["status"] != "running":
            return record
        time.sleep(2.0)
    pytest.fail("the analysis never finished")


# ------------------------------------------------------------------ preprocessing


def test_preprocessing_report_explains_what_fedot_changes(
    client: TestClient, dataset_uid: str
) -> None:
    response = client.get(f"/api/datasets/{dataset_uid}/preprocessing?task=classification")
    assert response.status_code == 200, response.text
    report = response.json()

    assert report["rows"]["before"] == 300
    assert report["source_types"], "no per-column information"

    # Everything is reported against the uploaded file's columns: one row and one
    # final type per file column, None where a column did not survive.
    assert len(report["final_types"]) == report["columns"]["before"]
    survivors = [t for t in report["final_types"] if t is not None]
    assert len(survivors) == report["columns"]["after"]
    assert [row["column"] for row in report["source_types"]] == list(
        range(report["columns"]["before"])
    )

    steps = {step["id"]: step for step in report["steps"]}
    assert {"empty_columns", "type_conflicts", "numeric_to_categorical"} <= set(steps)
    for step in report["steps"]:
        for column in step["columns"]:
            assert 0 <= column < report["columns"]["before"], step

    # The integer column with three distinct values should become categorical.
    assert steps["numeric_to_categorical"]["applied"], report["steps"]
    assert "str" in survivors

    # Gaps in the first column must be counted, not silently dropped.
    assert any(int(column.get("nan_number", 0)) > 0 for column in report["source_types"])


def test_preprocessing_needs_a_target(client: TestClient, tmp_path: Path) -> None:
    import pandas as pd

    path = tmp_path / "untargeted.csv"
    pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}).to_csv(path, index=False)
    with path.open("rb") as handle:
        uid = client.post(
            "/api/datasets", files={"file": ("untargeted.csv", handle, "text/csv")}
        ).json()["uid"]

    # The uploader guesses a target, so clear it to reach the error path.
    from fedotweb.settings import get_settings
    from fedotweb.storage.sqlite import Store

    store = Store(get_settings().database_path)
    record = store.get_dataset(uid)
    record["target"] = None
    store.save_dataset(record)

    response = client.get(f"/api/datasets/{uid}/preprocessing")
    assert response.status_code == 422
    assert "target" in response.json()["detail"].lower()


# -------------------------------------------------------------- objective detail


def test_objective_breakdown_reports_each_fold_and_the_holdout(
    client: TestClient, finished_run: str
) -> None:
    started = client.post(f"/api/runs/{finished_run}/analyses", json={"kind": "objective"})
    assert started.status_code == 202, started.text

    record = await_analysis(client, started.json()["uid"])
    assert record["status"] == "finished", record["error"]
    result = record["result"]

    assert result["cv_folds"] == 3
    assert len(result["folds"]) == 3
    assert result["primary_metric"] == "roc_auc"

    scored = [fold for fold in result["folds"] if not fold["failed"]]
    assert scored, "no fold produced a score"

    # The reported mean must actually be the mean of the folds -- that identity is
    # the whole claim the window makes.
    values = [fold["metrics"]["roc_auc"] for fold in scored if fold["metrics"].get("roc_auc")]
    assert values
    assert result["summary"]["roc_auc"]["mean"] == pytest.approx(sum(values) / len(values))
    assert result["summary"]["roc_auc"]["folds_used"] == len(values)

    # ROC AUC is maximised, so FEDOT stores it negated; the readable value flips back.
    summary = result["summary"]["roc_auc"]
    assert summary["is_maximised"] is True
    assert summary["readable_mean"] == pytest.approx(-summary["mean"])

    assert result["holdout"]["size"] > 0
    assert "roc_auc" in result["holdout"]["metrics"]


def test_analysis_is_listed_against_its_run(client: TestClient, finished_run: str) -> None:
    started = client.post(f"/api/runs/{finished_run}/analyses", json={"kind": "objective"})
    analysis_uid = started.json()["uid"]
    await_analysis(client, analysis_uid)

    listed = client.get(f"/api/runs/{finished_run}/analyses").json()
    assert any(item["uid"] == analysis_uid for item in listed)


def test_analysis_of_an_unknown_run_is_rejected(client: TestClient) -> None:
    assert client.post("/api/runs/nope/analyses", json={"kind": "objective"}).status_code == 404
    assert client.get("/api/analyses/nope").status_code == 404


# ------------------------------------------------------------------- sensitivity


def test_sensitivity_scores_every_node(client: TestClient, finished_run: str) -> None:
    started = client.post(
        f"/api/runs/{finished_run}/analyses",
        json={"kind": "sensitivity", "replacements": 1, "analyse_edges": False},
    )
    assert started.status_code == 202, started.text

    record = await_analysis(client, started.json()["uid"])
    assert record["status"] == "finished", record["error"]
    result = record["result"]

    assert result["metric"] == "roc_auc"
    nodes = [entity for entity in result["entities"] if entity["entity_type"] == "node"]
    assert nodes, "no node was analysed"

    for node in nodes:
        # Every node must be identifiable and carry a comparable number.
        assert node["operation"], node
        assert node["worst"] is None or isinstance(node["worst"].get("value"), (int, float))

        # The verdict is decided server-side: GOLEM's ratio is sign-normalised,
        # so `> 1` always means the change improved the objective.
        assert node["improves"] in (True, False, None)
        assert node["severity"] >= 0
        value = (node["worst"] or {}).get("value")
        if isinstance(value, (int, float)) and value != -1.0:
            assert node["improves"] is (value > 1)
