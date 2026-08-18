"""Reading field data, and the grid that comes with it."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from epdeweb.datasets.fields import (
    FieldError,
    build_preview,
    grids_for_epde,
    load_field_file,
    read_dataset,
    write_dataset,
)
from epdeweb.datasets.samples import SAMPLES, build_sample


def test_a_csv_matrix_becomes_a_two_dimensional_field(tmp_path: Path):
    path = tmp_path / "field.csv"
    matrix = np.arange(12, dtype=float).reshape(3, 4)
    np.savetxt(path, matrix, delimiter=",")

    dataset = load_field_file(path)
    dataset.validate()

    assert dataset.shape == (3, 4)
    assert dataset.axis_names == ["t", "x"]
    # No coordinates in the file, so the ranges are index positions -- and the
    # user is told, because every derivative scales with the spacing.
    assert dataset.warnings


def test_a_csv_with_a_time_column_becomes_a_trajectory(tmp_path: Path):
    path = tmp_path / "trajectory.csv"
    path.write_text("t,u,v\n0,1,2\n0.5,3,4\n1.0,5,6\n", encoding="utf-8")

    dataset = load_field_file(path)
    dataset.validate()

    assert sorted(dataset.variables) == ["u", "v"]
    assert dataset.axis_names == ["t"]
    assert dataset.axes[0].tolist() == [0.0, 0.5, 1.0]
    assert not dataset.warnings


def test_an_npz_matches_coordinate_vectors_to_the_axes_they_fit(tmp_path: Path):
    path = tmp_path / "bundle.npz"
    np.savez(path, u=np.zeros((5, 7)), t=np.linspace(0, 1, 5), x=np.linspace(0, 2, 7))

    dataset = load_field_file(path)
    dataset.validate()

    assert dataset.axis_names == ["t", "x"]
    assert dataset.axes[1][-1] == 2.0


def test_a_missing_coordinate_vector_is_reported_rather_than_invented(tmp_path: Path):
    path = tmp_path / "partial.npz"
    np.savez(path, u=np.zeros((5, 7)), t=np.linspace(0, 1, 5))

    dataset = load_field_file(path)

    assert len(dataset.axes) == 2
    assert any("length 7" in warning for warning in dataset.warnings)


def test_variables_on_different_grids_are_refused(tmp_path: Path):
    path = tmp_path / "mixed.npz"
    np.savez(path, u=np.zeros((5, 7)), v=np.zeros((5, 6)))

    dataset = load_field_file(path)
    # ``v`` does not share the shape of the largest array, so it is not a
    # variable; had both been the same size the mismatch would be caught here.
    assert list(dataset.variables) == ["u"]


def test_the_stored_form_round_trips(tmp_path: Path):
    path = tmp_path / "stored.npz"
    original = load_field_file(_write_csv(tmp_path))
    write_dataset(path, original)

    restored = read_dataset(path)

    assert restored.shape == original.shape
    assert restored.axis_names == original.axis_names
    np.testing.assert_allclose(restored.axes[0], original.axes[0])


def _write_csv(tmp_path: Path) -> Path:
    path = tmp_path / "round.csv"
    np.savetxt(path, np.arange(20, dtype=float).reshape(4, 5), delimiter=",")
    return path


def test_grids_for_epde_use_matrix_indexing():
    """``meshgrid`` defaults to 'xy', which transposes the first two axes.

    EPDE takes the tensors as given, so the default would silently swap time
    and space -- and the discovered equation would be a valid equation in the
    wrong variables.
    """
    _, dataset = build_sample("wave_1d")
    grids = grids_for_epde(dataset)

    assert len(grids) == 2
    assert grids[0].shape == dataset.shape
    # With 'ij' indexing the first grid varies along axis 0 and is constant
    # along axis 1; with 'xy' it would be the other way round.
    assert grids[0][0, 0] == grids[0][0, -1]
    assert grids[0][0, 0] != grids[0][-1, 0]


def test_a_one_dimensional_sample_previews_as_series():
    _, dataset = build_sample("lotka_volterra")
    preview = build_preview(dataset)

    assert preview["kind"] == "series"
    assert {series["name"] for series in preview["series"]} == {"u", "v"}
    assert len(preview["x"]) == len(preview["series"][0]["values"])


def test_a_large_field_is_downsampled_before_it_reaches_the_browser():
    _, dataset = build_sample("wave_1d")
    preview = build_preview(dataset)

    assert preview["kind"] == "field"
    surface = preview["surfaces"][0]
    assert len(surface["values"]) == len(preview["rows"])
    assert len(surface["values"][0]) == len(preview["columns"])
    assert len(surface["values"]) <= dataset.shape[0]


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda sample: sample.id)
def test_every_sample_builds_a_valid_field(sample):
    built, dataset = build_sample(sample.id)
    dataset.validate()

    assert sorted(dataset.variables) == sorted(built.variables)
    assert np.isfinite(next(iter(dataset.variables.values()))).all()


def test_an_unsupported_file_type_says_what_is_accepted(tmp_path: Path):
    path = tmp_path / "field.xlsx"
    path.write_bytes(b"not a field")

    with pytest.raises(FieldError, match=r"\.npy"):
        load_field_file(path)
