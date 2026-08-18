"""The HTTP surface, exercised without EPDE having to be installed."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from epdeweb.adapters import availability


@pytest.fixture()
def without_epde(monkeypatch: pytest.MonkeyPatch):
    """Pretend the framework is missing, whatever the test machine has.

    The module is meant to be servable without EPDE -- that is the whole point
    of keeping it a separate distribution -- so the behaviour is tested rather
    than left to whether CI happened to install it.
    """
    monkeypatch.setattr(
        availability,
        "_cached",
        availability.EpdeAvailability(available=False, error="EPDE is not installed."),
    )
    yield


def test_capabilities_reports_a_missing_epde_instead_of_failing(client, without_epde):
    payload = client.get("/api/capabilities").json()

    assert payload["epde_available"] is False
    assert "not installed" in payload["epde_error"]
    # The catalogue is still served: the screens that describe a run are
    # readable before anything is installed.
    assert [sample["id"] for sample in payload["samples"]]
    assert [family["id"] for family in payload["token_families"]]
    assert payload["controls"]


def test_starting_a_run_without_epde_is_refused_with_a_reason(client, without_epde):
    dataset = client.post("/api/datasets/samples/wave_1d").json()
    response = client.post(
        "/api/runs", json={"config": {"dataset_uid": dataset["uid"], "epochs": 1}}
    )

    assert response.status_code == 503
    assert "not installed" in response.json()["detail"]


def test_a_sample_is_created_once_and_reused(client):
    first = client.post("/api/datasets/samples/wave_1d").json()
    second = client.post("/api/datasets/samples/wave_1d").json()

    assert first["uid"] == second["uid"]
    assert first["shape"] == [81, 81]
    assert [axis["name"] for axis in first["axes"]] == ["t", "x"]


def test_an_unknown_sample_is_a_404(client):
    assert client.post("/api/datasets/samples/nope").status_code == 404


def test_uploading_a_field_reports_what_had_to_be_guessed(client):
    buffer = io.BytesIO()
    np.save(buffer, np.zeros((6, 8)))
    buffer.seek(0)

    response = client.post(
        "/api/datasets",
        files={"file": ("field.npy", buffer.getvalue(), "application/octet-stream")},
        data={"name": "bare array"},
    )

    assert response.status_code == 201
    record = response.json()
    assert record["shape"] == [6, 8]
    assert any("coordinates" in warning for warning in record["warnings"])


def test_setting_the_real_axis_ranges_rewrites_the_stored_grid(client):
    buffer = io.BytesIO()
    np.save(buffer, np.zeros((5, 4)))
    buffer.seek(0)
    uid = client.post(
        "/api/datasets", files={"file": ("field.npy", buffer.getvalue(), "application/octet-stream")}
    ).json()["uid"]

    response = client.patch(
        f"/api/datasets/{uid}/axes",
        json={"axes": [{"name": "t", "start": 0.0, "stop": 1.0}, {"name": "x", "start": -1.0, "stop": 1.0}]},
    )

    assert response.status_code == 200
    axes = response.json()["axes"]
    assert [axis["name"] for axis in axes] == ["t", "x"]
    assert axes[1]["start"] == -1.0 and axes[1]["stop"] == 1.0
    assert pytest.approx(axes[0]["step"]) == 0.25


def test_axis_names_must_be_distinct(client):
    uid = client.post("/api/datasets/samples/wave_1d").json()["uid"]
    response = client.patch(
        f"/api/datasets/{uid}/axes", json={"axes": [{"name": "t"}, {"name": "t"}]}
    )

    assert response.status_code == 422
    assert "distinct" in response.json()["detail"]


def test_a_wrong_number_of_axes_is_refused(client):
    uid = client.post("/api/datasets/samples/wave_1d").json()["uid"]
    response = client.patch(f"/api/datasets/{uid}/axes", json={"axes": [{"name": "t"}]})

    assert response.status_code == 422


def test_the_preview_of_a_field_is_a_downsampled_grid(client):
    uid = client.post("/api/datasets/samples/wave_1d").json()["uid"]
    preview = client.get(f"/api/datasets/{uid}/preview").json()

    assert preview["kind"] == "field"
    assert len(preview["surfaces"]) == 1
    assert len(preview["surfaces"][0]["values"]) == len(preview["rows"])


def test_deleting_a_dataset_removes_the_stored_field(client, workspace: Path):
    record = client.post("/api/datasets/samples/heat_1d").json()
    path = Path(record["filename"])
    assert path.exists()

    assert client.delete(f"/api/datasets/{record['uid']}").status_code == 204
    assert not path.exists()
    assert client.get(f"/api/datasets/{record['uid']}").status_code == 404


def test_unknown_runs_are_404_everywhere(client):
    for path in ("", "/progress", "/lineage", "/controls", "/result", "/events"):
        assert client.get(f"/api/runs/missing{path}").status_code == 404


def test_a_system_can_be_kept_under_its_own_name(client):
    graph = {"uid": "x", "text": "du/dt = u", "variables": ["u"]}
    created = client.post("/api/systems?name=my+equation", json=graph)

    assert created.status_code == 201
    uid = created.json()["uid"]
    assert client.get(f"/api/systems/{uid}").json()["name"] == "my equation"
    assert client.delete(f"/api/systems/{uid}").status_code == 204
    assert client.get(f"/api/systems/{uid}").status_code == 404


def test_a_run_config_with_an_empty_sparsity_interval_is_refused(client):
    """A multi-objective search evolves the sparsity constant inside the
    interval, so a degenerate one leaves it nothing to explore."""
    dataset = client.post("/api/datasets/samples/wave_1d").json()
    response = client.post(
        "/api/runs",
        json={
            "config": {
                "dataset_uid": dataset["uid"],
                "sparsity_min": 0.5,
                "sparsity_max": 0.5,
            }
        },
    )

    assert response.status_code in {422, 503}
