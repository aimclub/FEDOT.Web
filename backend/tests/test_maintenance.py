"""Housekeeping behaviours: restarts, deletions, and runs left without a worker."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _fresh_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FEDOTWEB_WORKSPACE", str(tmp_path / "workspace"))

    import fedotweb.settings as settings_module

    settings_module._settings = None  # noqa: SLF001 - reset the cached singleton

    from fedotweb.main import create_app

    return create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    create_app = _fresh_app(tmp_path, monkeypatch)
    with TestClient(create_app()) as test_client:
        yield test_client


def _store():
    from fedotweb.settings import get_settings
    from fedotweb.storage.sqlite import Store

    return Store(get_settings().database_path)


def test_interrupted_analyses_fail_instead_of_running_forever(client: TestClient) -> None:
    """An analysis orphaned by a restart would otherwise be polled indefinitely."""
    store = _store()
    run_uid = store.create_run(name="r", dataset_uid=None, config={})
    analysis_uid = store.create_analysis(
        run_uid=run_uid, kind="objective", pipeline_uid=None, options={}
    )
    assert store.get_analysis(analysis_uid)["status"] == "running"

    marked = store.fail_running_analyses("The server restarted")
    assert marked == 1

    record = store.get_analysis(analysis_uid)
    assert record["status"] == "failed"
    assert "restarted" in record["error"]
    assert record["finished_at"] is not None

    # Finished analyses are left alone.
    assert store.fail_running_analyses("again") == 0


def test_deleting_a_run_removes_its_analyses(client: TestClient) -> None:
    store = _store()
    run_uid = store.create_run(name="r", dataset_uid=None, config={})
    analysis_uid = store.create_analysis(
        run_uid=run_uid, kind="objective", pipeline_uid=None, options={}
    )

    store.delete_run(run_uid)
    assert store.get_analysis(analysis_uid) is None
    assert store.list_analyses(run_uid) == []


def test_a_run_without_a_worker_can_still_be_stopped(client: TestClient) -> None:
    """A dead attached script, or a worker lost to a crash, must not leave a run
    that shows as running forever with no way to end it from the GUI."""
    store = _store()
    run_uid = store.create_run(name="zombie", dataset_uid=None, config={"origin": "attached"})
    store.update_run(run_uid, status="running")

    response = client.post(f"/api/runs/{run_uid}/stop")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"

    # A graceful-finish request is left behind for a script that is still alive.
    from fedotweb.runs.control import read_controls
    from fedotweb.settings import get_settings

    assert read_controls(get_settings().runs_dir / run_uid).finish_now is True

    # Stopping a run that already ended stays a conflict.
    assert client.post(f"/api/runs/{run_uid}/stop").status_code == 409


def test_restart_fails_owned_runs_but_not_attached_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An attached run reports from the user's own process, which a GUI restart
    does not interrupt — declaring it failed would falsify a live run."""
    create_app = _fresh_app(tmp_path, monkeypatch)

    with TestClient(create_app()):
        store = _store()
        attached = store.create_run(name="attached", dataset_uid=None, config={"origin": "attached"})
        store.update_run(attached, status="running")
        managed = store.create_run(name="managed", dataset_uid=None, config={})
        store.update_run(managed, status="running")

    # A second startup over the same workspace is the restart.
    with TestClient(create_app()):
        store = _store()
        assert store.get_run(attached)["status"] == "running"
        assert store.get_run(managed)["status"] == "failed"


def test_event_kind_filter_matches_python_side_filtering(client: TestClient) -> None:
    store = _store()
    run_uid = store.create_run(name="r", dataset_uid=None, config={})
    for kind in ("generation", "population", "log", "generation", "effective_params"):
        store.append_event(run_uid, kind, {"kind": kind})

    generations = store.list_events(run_uid, kinds=["generation"])
    assert [event["kind"] for event in generations] == ["generation", "generation"]

    both = store.list_events(run_uid, kinds=["generation", "log"])
    assert [event["kind"] for event in both] == ["generation", "log", "generation"]

    assert len(store.list_events(run_uid)) == 5
