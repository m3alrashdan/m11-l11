"""Autograder: middleware behavior + ordering + label cardinality.

Maps to test plan rows:
  - test_request_counter_increments
  - test_latency_histogram_observes
  - test_request_id_header_present
  - test_structured_log_format
  - test_middleware_ordering
  - test_label_cardinality_safety
"""
import io
import json
import logging
import re

from fastapi.testclient import TestClient
import pytest

from api.main import app


client = TestClient(app)


def _scrape_metrics() -> str:
    return client.get("/metrics").text


def _counter_sample_for(body: str, path: str) -> float:
    """Return the requests_total sample value for the given path label, or 0.0."""
    # Pattern matches `requests_total{...path="<path>"...} <value>` (label order
    # does not matter — we look for path="<path>" anywhere in the label set).
    pattern = re.compile(
        r'^requests_total\{[^}]*path="' + re.escape(path) + r'"[^}]*\}\s+([0-9.eE+-]+)',
        re.MULTILINE,
    )
    m = pattern.search(body)
    return float(m.group(1)) if m else 0.0


def test_request_counter_increments():
    """After a request to /healthz, the counter for that path is >= 1.

    Catches buggy variant: metrics middleware not wired; wired after response
    sent; or no .inc() call.
    """
    before = _counter_sample_for(_scrape_metrics(), "/healthz")
    client.get("/healthz")
    after = _counter_sample_for(_scrape_metrics(), "/healthz")
    assert after >= before + 1, (
        f"requests_total for /healthz did not increment "
        f"(before={before}, after={after}). Is MetricsMiddleware wired and "
        "calling .labels(...).inc() on response?"
    )


def test_latency_histogram_observes():
    """After a request, the histogram has at least one bucket sample > 0.

    Catches buggy variant: histogram declared but .observe() not called.
    """
    client.get("/healthz")
    body = _scrape_metrics()
    # Find any request_latency_seconds_bucket sample with value > 0.
    pattern = re.compile(
        r'^request_latency_seconds_bucket\{[^}]+\}\s+([0-9.eE+-]+)',
        re.MULTILINE,
    )
    samples = [float(m) for m in pattern.findall(body)]
    assert samples, (
        "request_latency_seconds_bucket has no samples. Is the histogram "
        "declared and is MetricsMiddleware calling .observe(elapsed)?"
    )
    assert max(samples) > 0, (
        "All request_latency_seconds_bucket samples are 0. The histogram is "
        "declared but .observe() is not being called."
    )


def test_request_id_header_present():
    """Response has a non-empty X-Request-ID header.

    Catches buggy variant: request-id middleware missing.
    """
    resp = client.get("/healthz")
    header = resp.headers.get("x-request-id") or resp.headers.get("X-Request-ID")
    assert header is not None, (
        "Response missing X-Request-ID header. Is RequestIdMiddleware wired?"
    )
    assert len(header) >= 8, (
        f"X-Request-ID is too short ({header!r}); expected at least 8 chars."
    )


def test_structured_log_format(caplog):
    """Captured log includes a JSON line with request_id, path, status, latency_ms.

    Catches buggy variant: logging middleware uses print or text format.
    """
    # Capture from the root logger and any logger our middleware uses.
    with caplog.at_level(logging.INFO):
        client.get("/healthz")

    parsed_records = []
    for record in caplog.records:
        msg = record.getMessage()
        try:
            obj = json.loads(msg)
            parsed_records.append(obj)
        except (ValueError, TypeError):
            continue

    assert parsed_records, (
        "No JSON-parseable log line was captured. Is StructuredLoggingMiddleware "
        "emitting one JSON line per response (via the logging module)?"
    )

    required_keys = {"request_id", "path", "status", "latency_ms"}
    matched = [r for r in parsed_records if required_keys.issubset(set(r.keys()))]
    assert matched, (
        f"No JSON log line contained all required keys {sorted(required_keys)}. "
        f"Found JSON lines with keys: {[sorted(r.keys()) for r in parsed_records]}."
    )


def test_middleware_ordering(caplog):
    """The structured log line for a request contains the same request-id as the response header.

    Catches buggy variant: wrong middleware order (request-id is not outer of
    logging, so the log line does not see the request id).
    """
    with caplog.at_level(logging.INFO):
        resp = client.get("/healthz")

    response_request_id = resp.headers.get("x-request-id") or resp.headers.get("X-Request-ID")
    assert response_request_id, "X-Request-ID header missing; cannot verify ordering."

    found = False
    for record in caplog.records:
        msg = record.getMessage()
        try:
            obj = json.loads(msg)
        except (ValueError, TypeError):
            continue
        if obj.get("request_id") == response_request_id:
            found = True
            break

    assert found, (
        "No log line carried the same request_id as the response header. "
        "Middleware order should be request-id outermost (added LAST), "
        "structured-logging middle, metrics innermost."
    )


def test_label_cardinality_safety():
    """`requests_total` label names are a subset of {path, status, method}.

    Catches buggy variant: learner added a high-cardinality label (user_id,
    query_text, full URL).
    """
    body = _scrape_metrics()
    # Find any requests_total line and parse its labelnames.
    pattern = re.compile(r'^requests_total\{([^}]*)\}', re.MULTILINE)
    label_blob = pattern.search(body)
    # If no samples have been emitted yet, parse the # HELP / # TYPE block — the
    # client library reflects declared labelnames as the label set on the first
    # observed sample only. Force a sample first.
    if not label_blob:
        client.get("/healthz")
        body = _scrape_metrics()
        label_blob = pattern.search(body)

    assert label_blob, (
        "requests_total has no observed samples; could not verify label names. "
        "Is MetricsMiddleware wired and incrementing the counter?"
    )

    labels = label_blob.group(1)
    label_names = set(re.findall(r'(\w+)="', labels))
    required = {"path", "status"}
    missing = required - label_names
    assert not missing, (
        f"requests_total is missing required labels: {missing}. The Lab "
        f"guide specifies labels=['path', 'status'] -- both must be present."
    )
    extra = label_names - required
    assert not extra, (
        f"requests_total has disallowed labels: {extra}. The Lab guide "
        f"specifies labels=['path', 'status'] only -- additional labels "
        f"produce extra timeseries (a label-set drift bug). Keep labels "
        f"within {required}."
    )
