"""Observability layer for the M10 backend.

This module is where you (the learner) declare the three Prometheus metric
families and implement the three ASGI middleware classes that the autograder
exercises through the FastAPI app.

What lives here, and why:

  - Three metric families. A counter for request volume by (path, status), a
    histogram for request latency by path, and a gauge for in-flight requests.
    Together they answer "how much traffic, how slow, how concurrent."

  - Three middlewares. A request-id layer that attaches a per-request
    correlation id to the response and to the logging context. A
    structured-logging layer that emits one JSON line per response. A metrics
    layer that increments the counter, observes the latency histogram, and
    brackets the request with the in-flight gauge.

  Ordering matters: request-id is outermost (so it wraps the logging line),
  logging is middle, metrics is innermost (closest to the route).

Where to put what:

  - Declarations at MODULE SCOPE. If you declare a Counter / Histogram / Gauge
    inside a function or inside a middleware __call__, you will hit
    `Duplicated timeseries in CollectorRegistry` on the second request --
    every request re-runs the function. Module scope means the registry sees
    the declaration once at import time.

  - Label cardinality matters. The Lab's `requests_total` Counter uses
    exactly two labels: {path, status}. Do NOT add user-id, query-text,
    full-URL, or any other unbounded label.

Methodology pointers:

  - Reading sections 6-10 cover middleware, metric types, label cardinality.
  - See Common Pitfalls #1-#4 in the lab guide.
"""

# TODO: import Counter, Histogram, Gauge from prometheus_client.

# TODO: declare the three metric families at module scope.
#
#   requests_total           — Counter, labels (path, status)
#   request_latency_seconds  — Histogram, label (path); use the default
#                              Prometheus latency buckets.
#   inflight_requests        — Gauge, no labels.
#
# Do not over-label — see the cardinality discussion in the M11 reading.


# TODO: implement RequestIdMiddleware (ASGI middleware class).
#
#   - __init__(self, app): store app.
#   - __call__(self, scope, receive, send): generate a request id, store it
#     somewhere the logging layer can read (a ContextVar is the standard
#     pattern), and arrange for the outbound response to carry an
#     `X-Request-ID` header.
#
#   The autograder asserts the response header is present and at least 8
#   characters long.


# TODO: implement StructuredLoggingMiddleware (ASGI middleware class).
#
#   - On response, emit one JSON line containing the keys:
#       request_id, path, status, latency_ms
#     plus any other keys you find useful. The autograder asserts the four
#     keys above are present and parseable as JSON.


# TODO: implement MetricsMiddleware (ASGI middleware class).
#
#   - On request: increment inflight_requests.
#   - Around the route handler: time the request.
#   - On response: increment requests_total with the (path, status) label
#     pair, observe the latency histogram, decrement inflight_requests.
#
#   Do not include high-cardinality labels (no user id, no query string).
