import pytest

from src.diff import diff_shapes, infer_shape


def test_infer_shape_basic_types():
    payload = {
        "id": 1,
        "active": True,
        "score": 3.5,
        "name": "flyrank",
        "tags": ["a", "b"],
        "meta": {"k": "v"},
        "deleted_at": None,
    }
    shape = infer_shape(payload)
    assert shape == {
        "id": "integer",
        "active": "boolean",
        "score": "number",
        "name": "string",
        "tags": "array",
        "meta": "object",
        "deleted_at": "null",
    }


def test_infer_shape_bool_not_confused_with_int():
    # bool is a subclass of int in Python; this guards against misclassifying it.
    shape = infer_shape({"flag": True})
    assert shape["flag"] == "boolean"


def test_infer_shape_rejects_non_object():
    with pytest.raises(TypeError):
        infer_shape([1, 2, 3])  # type: ignore[arg-type]


def test_diff_no_changes():
    shape = {"id": "integer", "email": "string"}
    report = diff_shapes(shape, dict(shape))
    assert not report.has_drift
    assert report.added_fields == []
    assert report.removed_fields == []
    assert report.type_changes == []


def test_diff_detects_added_and_removed_fields():
    baseline = {"id": "integer", "email": "string", "is_active": "boolean"}
    current = {"id": "integer", "email": "string", "account_tier": "string"}
    report = diff_shapes(baseline, current)
    assert report.has_drift
    assert report.added_fields == ["account_tier"]
    assert report.removed_fields == ["is_active"]


def test_diff_detects_type_change():
    baseline = {"id": "integer"}
    current = {"id": "string"}
    report = diff_shapes(baseline, current)
    assert report.has_drift
    assert report.type_changes == ["'id': integer -> string"]
