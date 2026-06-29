"""Autograder: /metrics endpoint + metric family declarations.

Maps to test plan rows:
  - test_metrics_endpoint_returns_200
  - test_three_metric_families_declared
"""
from fastapi.testclient import TestClient
import pytest

from api.main import app


client = TestClient(app)


def test_metrics_endpoint_returns_200():
    """`/metrics` is mounted and serves an OpenMetrics text response.

    Catches buggy variant: learner forgot `app.mount("/metrics", make_asgi_app())`.
    """
    resp = client.get("/metrics")
    assert resp.status_code == 200, (
        f"GET /metrics returned {resp.status_code}; expected 200. "
        "Did you mount /metrics with make_asgi_app()?"
    )
    ctype = resp.headers.get("content-type", "")
    assert "text/plain" in ctype, (
        f"/metrics content-type was {ctype!r}; expected text/plain (OpenMetrics)."
    )


def test_three_metric_families_declared():
    """`requests_total`, `request_latency_seconds`, `inflight_requests` all present.

    Catches buggy variant: one or more metric declarations missing.
    """
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    missing = []
    for name in ("requests_total", "request_latency_seconds", "inflight_requests"):
        if name not in body:
            missing.append(name)
    assert not missing, (
        f"Missing metric families in /metrics body: {missing}. "
        "Declare all three at module scope in api/observability.py."
    )
