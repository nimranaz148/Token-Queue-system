import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.logging import StructuredJsonFormatter
from app.main import app

client = TestClient(app)


class InMemoryLogHandler(logging.Handler):
    """Handler that captures formatted log messages and records in memory."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []
        self.formatted_entries: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        if self.formatter:
            self.formatted_entries.append(self.formatter.format(record))


@pytest.fixture
def log_capture() -> InMemoryLogHandler:
    handler = InMemoryLogHandler()
    formatter = StructuredJsonFormatter()
    handler.setFormatter(formatter)

    # Attach to app.access and app.errors loggers
    access_logger = logging.getLogger("app.access")
    errors_logger = logging.getLogger("app.errors")

    access_logger.addHandler(handler)
    errors_logger.addHandler(handler)
    access_logger.setLevel(logging.DEBUG)
    errors_logger.setLevel(logging.DEBUG)

    yield handler

    access_logger.removeHandler(handler)
    errors_logger.removeHandler(handler)


def test_successful_request_propagates_request_id(log_capture: InMemoryLogHandler) -> None:
    custom_req_id = "req-custom-trace-12345"
    response = client.get("/api/v1/health", headers={"x-request-id": custom_req_id})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_req_id

    # Verify log capture has a record with this exact request_id
    matching_records = [
        r for r in log_capture.records if getattr(r, "request_id", None) == custom_req_id
    ]
    assert len(matching_records) > 0
    assert matching_records[0].status_code == 200


def test_generated_request_id_when_missing(log_capture: InMemoryLogHandler) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    res_req_id = response.headers.get("x-request-id")
    assert res_req_id is not None
    # Validate it is a valid UUID
    uuid.UUID(res_req_id)

    matching_records = [
        r for r in log_capture.records if getattr(r, "request_id", None) == res_req_id
    ]
    assert len(matching_records) > 0


def test_failed_request_traceable_to_log_line(log_capture: InMemoryLogHandler) -> None:
    """Acceptance criterion for Task 41:

    A failed request can be traced from the response id to the log line.
    """
    response = client.get("/api/v1/doctors")
    assert response.status_code == 401

    # Get request ID from response header and problem details body
    header_req_id = response.headers.get("x-request-id")
    assert header_req_id is not None

    body_data = response.json()
    assert body_data.get("request_id") == header_req_id
    assert body_data["code"] == "UNAUTHORIZED"

    # Find the matching log lines by response id
    matching_logs = [
        entry for entry in log_capture.formatted_entries if f'"{header_req_id}"' in entry
    ]
    assert len(matching_logs) > 0

    # Parse JSON structured log to verify tracing fields
    parsed_log = json.loads(matching_logs[0])
    assert parsed_log["request_id"] == header_req_id
    assert parsed_log["path"] == "/api/v1/doctors"
    assert parsed_log["status_code"] == 401


def test_structured_json_formatter_emits_valid_json() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=100,
        msg="Test error event",
        args=(),
        exc_info=None,
    )
    record.request_id = "trace-id-abc"  # type: ignore[attr-defined]
    record.method = "POST"  # type: ignore[attr-defined]
    record.path = "/api/v1/tokens"  # type: ignore[attr-defined]
    record.status_code = 422  # type: ignore[attr-defined]
    record.duration_ms = 12.34  # type: ignore[attr-defined]
    record.client_ip = "192.168.1.1"  # type: ignore[attr-defined]

    formatter = StructuredJsonFormatter()
    output = formatter.format(record)

    data = json.loads(output)
    assert data["level"] == "ERROR"
    assert data["message"] == "Test error event"
    assert data["request_id"] == "trace-id-abc"
    assert data["method"] == "POST"
    assert data["path"] == "/api/v1/tokens"
    assert data["status_code"] == 422
    assert data["duration_ms"] == 12.34
    assert data["client_ip"] == "192.168.1.1"
