import pytest

from src.schema import FieldSpec, Schema


def make_schema(allow_extra: bool = True) -> Schema:
    return Schema(
        name="test_schema",
        allow_extra_fields=allow_extra,
        fields=[
            FieldSpec(name="id", type="integer", required=True),
            FieldSpec(name="email", type="string", required=True),
            FieldSpec(name="nickname", type="string", required=False, nullable=True),
            FieldSpec(name="is_active", type="boolean", required=True),
        ],
    )


def test_valid_payload_passes():
    schema = make_schema()
    payload = {"id": 1, "email": "a@example.com", "nickname": None, "is_active": True}
    result = schema.validate(payload)
    assert result.is_valid
    assert result.errors == []


def test_missing_required_field_fails():
    schema = make_schema()
    payload = {"email": "a@example.com", "is_active": True}
    result = schema.validate(payload)
    assert not result.is_valid
    assert any("id" in e for e in result.errors)


def test_wrong_type_fails():
    schema = make_schema()
    payload = {"id": "not-an-int", "email": "a@example.com", "is_active": True}
    result = schema.validate(payload)
    assert not result.is_valid
    assert any("id" in e and "expected type" in e for e in result.errors)


def test_null_on_non_nullable_field_fails():
    schema = make_schema()
    payload = {"id": 1, "email": None, "is_active": True}
    result = schema.validate(payload)
    assert not result.is_valid
    assert any("email" in e and "nullable" in e for e in result.errors)


def test_extra_field_is_warning_when_allowed():
    schema = make_schema(allow_extra=True)
    payload = {"id": 1, "email": "a@example.com", "is_active": True, "extra": "x"}
    result = schema.validate(payload)
    assert result.is_valid
    assert any("extra" in w for w in result.warnings)


def test_extra_field_is_error_when_disallowed():
    schema = make_schema(allow_extra=False)
    payload = {"id": 1, "email": "a@example.com", "is_active": True, "extra": "x"}
    result = schema.validate(payload)
    assert not result.is_valid
    assert any("extra" in e for e in result.errors)


def test_non_object_payload_fails_cleanly():
    schema = make_schema()
    result = schema.validate(["not", "an", "object"])  # type: ignore[arg-type]
    assert not result.is_valid
    assert "object" in result.errors[0]


def test_unknown_type_rejected_at_construction():
    with pytest.raises(ValueError):
        FieldSpec(name="bad", type="not-a-real-type")


def test_schema_requires_at_least_one_field():
    with pytest.raises(ValueError):
        Schema(name="empty", fields=[])
