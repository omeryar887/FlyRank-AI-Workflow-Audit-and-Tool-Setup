import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings
from src.schema import FieldSpec, Schema
from src.validator import (
    ApiContractValidator,
    PayloadRetrievalError,
    fetch_payload_from_endpoint,
    load_payload_from_file,
)


@pytest.fixture
def schema() -> Schema:
    return Schema(
        name="test_schema",
        fields=[
            FieldSpec(name="id", type="integer", required=True),
            FieldSpec(name="email", type="string", required=True),
        ],
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_base_url="https://example.internal/api",
        api_auth_token="dummy-token-for-tests",
        request_timeout_seconds=5.0,
        output_dir=Path("./reports"),
        log_level="INFO",
    )


def test_load_payload_from_file_missing_file(tmp_path):
    with pytest.raises(PayloadRetrievalError):
        load_payload_from_file(tmp_path / "does_not_exist.json")


def test_load_payload_from_file_bad_json(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(PayloadRetrievalError):
        load_payload_from_file(bad_file)


def test_load_payload_from_file_valid(tmp_path):
    good_file = tmp_path / "good.json"
    good_file.write_text(json.dumps({"id": 1, "email": "a@example.com"}), encoding="utf-8")
    result = load_payload_from_file(good_file)
    assert result.payload == {"id": 1, "email": "a@example.com"}
    assert result.source == f"file:{good_file}"


def test_validate_file_end_to_end(tmp_path, schema):
    good_file = tmp_path / "good.json"
    good_file.write_text(json.dumps({"id": 1, "email": "a@example.com"}), encoding="utf-8")
    validator = ApiContractValidator(schema)
    result, fetched = validator.validate_file(good_file)
    assert result.is_valid
    assert fetched.source.startswith("file:")


def test_endpoint_path_rejects_full_url(settings):
    with pytest.raises(ValueError):
        fetch_payload_from_endpoint(settings, "https://not-allowed.example.com/x")


@patch("src.validator.requests.get")
def test_fetch_payload_from_endpoint_success(mock_get, settings):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 1, "email": "a@example.com"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_payload_from_endpoint(settings, "/v1/users/1")

    assert result.payload == {"id": 1, "email": "a@example.com"}
    assert result.source == "http:https://example.internal/api/v1/users/1"

    called_url = mock_get.call_args.args[0]
    called_headers = mock_get.call_args.kwargs["headers"]
    assert called_url == "https://example.internal/api/v1/users/1"
    assert called_headers["Authorization"] == "Bearer dummy-token-for-tests"


@patch("src.validator.requests.get")
def test_fetch_payload_from_endpoint_http_error_wrapped(mock_get, settings):
    import requests

    mock_get.side_effect = requests.exceptions.ConnectionError("boom")
    with pytest.raises(PayloadRetrievalError):
        fetch_payload_from_endpoint(settings, "/v1/users/1")
