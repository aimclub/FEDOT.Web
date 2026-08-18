"""An end-to-end search, through the API, against the real framework.

Skipped when EPDE is not installed. It is the only test that proves the whole
chain -- worker, instrumentation, saved history, lineage endpoint -- works
against the framework rather than against the stand-ins, and it is the test that
catches the things stand-ins cannot: which vector EPDE fills, which way round
its weights are stored, what its derivative labels mean.
"""

from __future__ import annotations

import time

import pytest

from epdeweb.adapters.availability import describe_epde

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not describe_epde().available, reason="EPDE is not installed"),
]

#: Long enough for a small search on the 81x81 wave field, short enough to keep
#: the suite usable. The run also carries its own budget, so it ends by itself.
TIMEOUT_SECONDS = 300


def wait_for(client, uid: str) -> dict:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        record = client.get(f"/api/runs/{uid}").json()
        if record["status"] in {"finished", "failed", "cancelled"}:
            return record
        time.sleep(1.0)
    pytest.fail(f"the run did not finish within {TIMEOUT_SECONDS}s")


def test_a_wave_field_yields_a_second_order_equation(client):
    dataset = client.post("/api/datasets/samples/wave_1d").json()

    started = client.post(
        "/api/runs",
        json={
            "name": "wave",
            "config": {
                "dataset_uid": dataset["uid"],
                "multiobjective": True,
                "population_size": 6,
                "epochs": 2,
                "timeout": 4,
                "max_deriv_order": [2, 2],
                "equation_terms_max_number": 4,
                "equation_factors_max_number": 1,
                "boundary": 10,
                "seed": 7,
            },
        },
    )
    assert started.status_code == 202
    uid = started.json()["uid"]

    record = wait_for(client, uid)
    assert record["status"] == "finished", record["error"]

    result = client.get(f"/api/runs/{uid}/result").json()
    assert result["front"], "the search returned an empty Pareto front"
    assert result["generations"] >= 1

    # The axes are named after the dataset, not after EPDE's positional x0/x1.
    text = result["front"][0]["text"]
    assert "/dx" not in text or "dx0" not in text
    assert any(name in text for name in ("dt", "dx"))

    # A second-order field should be described by a second-order equation.
    assert "d^2u" in " ".join(entry["text"] for entry in result["front"])


def test_the_saved_history_answers_the_lineage_endpoints(client):
    dataset = client.post("/api/datasets/samples/heat_1d").json()
    uid = client.post(
        "/api/runs",
        json={
            "config": {
                "dataset_uid": dataset["uid"],
                "population_size": 6,
                "epochs": 2,
                "timeout": 4,
                "max_deriv_order": [1, 2],
                "equation_terms_max_number": 4,
                "boundary": 6,
                "seed": 3,
            }
        },
    ).json()["uid"]

    record = wait_for(client, uid)
    assert record["status"] == "finished", record["error"]

    lineage = client.get(f"/api/runs/{uid}/lineage").json()
    assert lineage["source"] == "history" and lineage["is_live"] is False
    assert lineage["nodes"], "the genealogy is empty"
    assert lineage["objective_names"]

    individuals = [node for node in lineage["nodes"] if node["kind"] == "individual"]
    assert individuals

    # Every node in the genealogy can be opened, which is what makes it worth
    # drawing rather than just counting.
    described = client.get(f"/api/runs/{uid}/lineage/{individuals[0]['uid']}")
    assert described.status_code == 200
    assert described.json()["equations"]

    full = client.get(f"/api/runs/{uid}/lineage?full=true").json()
    assert len(full["nodes"]) >= len(lineage["nodes"])


def test_progress_reports_the_objective_curves_and_the_front(client):
    dataset = client.post("/api/datasets/samples/transport_1d").json()
    uid = client.post(
        "/api/runs",
        json={
            "config": {
                "dataset_uid": dataset["uid"],
                "population_size": 6,
                "epochs": 2,
                "timeout": 4,
                "max_deriv_order": [1, 1],
                "equation_terms_max_number": 4,
                "boundary": 8,
                "seed": 5,
            }
        },
    ).json()["uid"]

    record = wait_for(client, uid)
    assert record["status"] == "finished", record["error"]

    progress = client.get(f"/api/runs/{uid}/progress").json()
    assert progress["generations"], "no generation was reported"
    assert progress["objective_names"]
    assert progress["best_system"]["text"]

    first = progress["generations"][0]
    assert first["objectives"], "a generation with no objective summary"
    assert first["size"] > 0
