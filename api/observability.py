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
import json
import logging
import time
import uuid
from contextvars import ContextVar

from prometheus_client import Counter, Gauge, Histogram
from starlette.datastructures import MutableHeaders

# ---------------------------------------------------------------------------
# Metric families (declared once, at module scope, so the default registry
# sees each declaration a single time at import).
# ---------------------------------------------------------------------------

# How much traffic, broken down by route template and response status. Both
# labels are bounded: `path` is the matched route (never the raw URL with its
# query string or path params), `status` is an HTTP status code.
requests_total = Counter(
    "requests_total",
    "Total HTTP requests processed, labeled by route template and status code.",
    ["path", "status"],
)

# How slow, per route. No explicit buckets => prometheus_client's default
# latency buckets (.005 .. 10.0, +Inf) which target sub-second web latencies.
request_latency_seconds = Histogram(
    "request_latency_seconds",
    "HTTP request latency in seconds, labeled by route template.",
    ["path"],
)

# How concurrent. A single gauge, no labels: incremented on entry, decremented
# on exit, so its instantaneous value is the number of in-flight requests.
inflight_requests = Gauge(
    "inflight_requests",
    "Number of HTTP requests currently being processed.",
)


# ---------------------------------------------------------------------------
# Correlation id. RequestIdMiddleware sets this on entry; the structured
# logging layer (which is nested inside request-id) reads it for the log line.
# A ContextVar is the standard pattern: it is task-local, so concurrent
# requests do not see each other's id.
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_logger = logging.getLogger("m11.api")


def _route_path(scope) -> str:
    """Return the matched route template for `scope`, falling back to the raw path.

    Using the route template (e.g. ``/items/{id}``) rather than the raw path
    (``/items/42``) keeps the `path` label cardinality bounded: one timeseries
    per route, not one per distinct URL. The Lab's routes are all static, so
    the template and the raw path coincide, but preferring the template is the
    correct production habit.
    """
    route = scope.get("route")
    template = getattr(route, "path", None)
    return template or scope.get("path", "")


class RequestIdMiddleware:
    """Attach a per-request correlation id to the context and the response.

    Generates ``uuid.uuid4().hex`` on entry, stores it in ``request_id_var`` so
    the nested logging layer can read it, and sets the ``X-Request-ID`` response
    header by wrapping ``send`` and editing the ``http.response.start`` headers.
    Must be the OUTERMOST of the three middlewares so the id is set before the
    logging layer emits its line.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        token = request_id_var.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)


class StructuredLoggingMiddleware:
    """Emit exactly one JSON log line per response.

    The line always carries ``request_id``, ``path``, ``status`` and
    ``latency_ms`` (the four keys the autograder asserts), plus ``ts`` and
    ``level`` as best-practice context. The starter does not install a JSON
    formatter, so we format the line ourselves with ``json.dumps`` and hand the
    finished string to ``logging.getLogger("m11.api").info``.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = {"value": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency_ms = (time.perf_counter() - start) * 1000.0
            _logger.info(
                json.dumps(
                    {
                        "ts": time.time(),
                        "level": "INFO",
                        "request_id": request_id_var.get(""),
                        "path": _route_path(scope),
                        "status": status_code["value"],
                        "latency_ms": round(latency_ms, 3),
                    }
                )
            )


class MetricsMiddleware:
    """Record the three Prometheus metrics for every HTTP request.

    Brackets the request with the in-flight gauge (inc on entry, dec on exit in
    a ``finally`` so a raising handler still decrements), times the handler, and
    on completion increments ``requests_total`` for the ``(path, status)`` pair
    and observes ``request_latency_seconds`` for the path. Must be the
    INNERMOST of the three middlewares so the latency it measures is the route
    handler's, not the cost of the logging/request-id layers around it.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_code = {"value": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
            await send(message)

        inflight_requests.inc()
        start = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - start
            inflight_requests.dec()
            path = _route_path(scope)
            requests_total.labels(path=path, status=str(status_code["value"])).inc()
            request_latency_seconds.labels(path=path).observe(elapsed)
