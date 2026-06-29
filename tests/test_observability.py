"""YOUR tests for the observability layer.

Three behaviors are exercised here, one per middleware:

  1. RequestIdMiddleware sets a non-empty ``X-Request-ID`` response header.
  2. MetricsMiddleware increments ``requests_total`` for the request's
     ``(path, status)`` pair.
  3. StructuredLoggingMiddleware emits a JSON line whose ``request_id`` matches
     the ``X-Request-ID`` header -- proving request-id is wired OUTSIDE logging
     (correct ordering) and that the correlation id flows from header to log.
"""
import json
import logging
import re

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def _requests_total_for(body: str, path: str) -> float:
    """Return the requests_total sample value for the given path label, or 0.0."""
    pattern = re.compile(
        r'^requests_total\{[^}]*path="' + re.escape(path) + r'"[^}]*\}\s+([0-9.eE+-]+)',
        re.MULTILINE,
    )
    match = pattern.search(body)
    return float(match.group(1)) if match else 0.0


def test_request_id_header_is_set_and_nonempty():
    """Every response carries a non-empty X-Request-ID correlation header."""
    resp = client.get("/healthz")
    request_id = resp.headers.get("x-request-id")
    assert request_id is not None, "X-Request-ID header missing from response"
    assert request_id != "", "X-Request-ID header is empty"


def test_requests_total_counter_increments():
    """A request to /healthz bumps requests_total for that (path, status)."""
    before = _requests_total_for(client.get("/metrics").text, "/healthz")
    client.get("/healthz")
    after = _requests_total_for(client.get("/metrics").text, "/healthz")
    assert after >= before + 1, (
        f"requests_total for /healthz did not increment (before={before}, after={after})"
    )


def test_structured_log_request_id_matches_header(caplog):
    """The JSON log line carries the same request_id as the response header."""
    with caplog.at_level(logging.INFO, logger="m11.api"):
        resp = client.get("/healthz")
    header_id = resp.headers.get("x-request-id")
    assert header_id, "X-Request-ID header missing; cannot correlate the log line"

    logged_ids = []
    for record in caplog.records:
        try:
            logged_ids.append(json.loads(record.getMessage()).get("request_id"))
        except (ValueError, TypeError):
            continue
    assert header_id in logged_ids, (
        "No structured log line carried the response's request_id; "
        f"header={header_id!r}, logged ids={logged_ids!r}"
    )
