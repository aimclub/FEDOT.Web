"""The hyperparameter schemas are what the UI's typed editor is built on."""

from __future__ import annotations

import json

import pytest

from fedotweb.catalog import get_catalog


@pytest.fixture(scope="module")
def catalog():
    return get_catalog()


def test_catalogue_covers_models_and_data_operations(catalog) -> None:
    operations = catalog.list_operations()
    kinds = {operation["kind"] for operation in operations}

    assert len(operations) > 50
    assert {"model", "data_operation"} <= kinds
    assert {operation["id"] for operation in operations} >= {"rf", "logit", "scaling", "pca"}


def test_task_filter_excludes_incompatible_operations(catalog) -> None:
    classification = {op["id"] for op in catalog.list_operations(task="classification")}
    forecasting = {op["id"] for op in catalog.list_operations(task="ts_forecasting")}

    assert "logit" in classification
    assert "logit" not in forecasting
    assert "lagged" in forecasting


def test_unknown_task_is_rejected(catalog) -> None:
    with pytest.raises(ValueError):
        catalog.list_operations(task="nonsense")


def test_continuous_parameter_carries_its_sampling_scope(catalog) -> None:
    parameters = {p["name"]: p for p in catalog.get("rf")["parameters"]}

    max_features = parameters["max_features"]
    assert max_features["type"] == "continuous"
    assert max_features["tunable"] is True
    assert max_features["minimum"] == pytest.approx(0.05)
    assert max_features["maximum"] == pytest.approx(1.0)
    assert max_features["value_type"] == "number"


def test_discrete_and_categorical_parameters(catalog) -> None:
    parameters = {p["name"]: p for p in catalog.get("rf")["parameters"]}

    assert parameters["min_samples_split"]["type"] == "discrete"
    assert parameters["min_samples_split"]["value_type"] == "integer"

    criterion = parameters["criterion"]
    assert criterion["type"] == "categorical"
    assert criterion["choices"] == ["gini", "entropy"]


def test_log_scale_is_detected(catalog) -> None:
    """`hp.loguniform` scopes must be flagged so the slider can be logarithmic."""
    learning_rate = next(
        p for p in catalog.get("adareg")["parameters"] if p["name"] == "learning_rate"
    )
    assert learning_rate["distribution"] == "loguniform"
    assert learning_rate["log_scale"] is True


def test_defaults_are_merged_into_the_schema(catalog) -> None:
    n_components = next(
        p for p in catalog.get("pca")["parameters"] if p["name"] == "n_components"
    )
    assert n_components["default"] == pytest.approx(0.7)
    assert n_components["minimum"] is not None and n_components["maximum"] is not None


def test_parameters_with_only_a_default_are_still_editable(catalog) -> None:
    """`n_jobs` is not tuned, but the user must still be able to change it."""
    n_jobs = next(p for p in catalog.get("rf")["parameters"] if p["name"] == "n_jobs")
    assert n_jobs["tunable"] is False
    assert n_jobs["default"] == 1
    assert n_jobs["value_type"] == "integer"


def test_nested_search_space_is_decoded(catalog) -> None:
    """`glm` nests its parameters; each variant must expose its own options."""
    nested = next(p for p in catalog.get("glm")["parameters"] if p["type"] == "nested")

    labels = {variant["label"] for variant in nested["nested_variants"]}
    assert labels == {"gaussian", "gamma", "inverse_gaussian"}

    gaussian = next(v for v in nested["nested_variants"] if v["label"] == "gaussian")
    assert gaussian["fixed"] == {"family": "gaussian"}
    assert gaussian["options"]["link"] == ["identity", "inverse_power", "log"]


def test_every_schema_is_json_serialisable(catalog) -> None:
    """Nothing may leak a hyperopt object, NaN or infinity into the API payload."""
    for operation in catalog.list_operations(with_parameters=True):
        json.dumps(operation, allow_nan=False)


def test_unknown_operation_returns_none(catalog) -> None:
    assert catalog.get("no_such_operation") is None
    assert catalog.exists("no_such_operation") is False
