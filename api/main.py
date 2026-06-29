"""FastAPI backend for the M11 Lab — vendored M10 backend + M11 instrumentation slots.

What you (the learner) do in this file:

  1. Wire the three middlewares from ``api/observability.py`` onto ``app`` in
     the correct order (request-id outermost, structured-logging middle,
     metrics innermost — closest to the route).
  2. Mount ``/metrics`` using ``prometheus_client.make_asgi_app()``.

The four backend endpoints (``/healthz``, ``/readyz``, ``/extract``,
``/kg/query``, ``/rag/answer``) are already wired here, vendored from the
M10 deliverable. They run against the live four-service docker-compose
stack (Neo4j, Weaviate, ``api``, ``web``) when external clients can be
constructed at startup; when run in CI / TestClient without those services
configured, the lifespan logs a degraded-mode warning and the endpoints
return small deterministic stubs so the autograder's import-time test
surface (``/healthz``, ``/metrics``, middleware behavior) works without
docker.

Read ``api/observability.py`` for the methodology and where the symbols
come from. Read ``api/rag.py`` + ``api/kg.py`` + ``api/nlp.py`` for the
vendored M10 reference implementations.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# TODO (learner): import the three middleware classes from api.observability.
# Hint: RequestIdMiddleware, StructuredLoggingMiddleware, MetricsMiddleware.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# TODO (learner): import make_asgi_app from prometheus_client so you can
# mount /metrics below.
# ---------------------------------------------------------------------------

from .deps import get_generator, get_nlp, get_session, get_weaviate
from .kg import wrap_kg_query
from .models import (
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    UnsupportedQueryDetail,
)
from .nlp import extract_entities
from .rag import compose_rag
from .w9b_mapper.errors import UnsupportedQueryError
from .w9b_mapper.shapes import SUPPORTED_PATTERNS


_logger = logging.getLogger("m11.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Construct process-scoped resources for the live stack.

    Vendored M10 lifespan with M11 resilience: each external client is
    constructed in a try/except so the FastAPI app can still import and
    serve ``/healthz`` + ``/metrics`` when Neo4j / Weaviate / spaCy /
    transformers are not available (the autograder unit-test surface).
    When a client is unavailable the corresponding endpoint returns a
    small deterministic stub; the live stack (``docker compose up -d``)
    constructs every client successfully and serves real M10 behavior.
    """
    app.state.neo4j_driver = None
    app.state.weaviate_client = None
    app.state.nlp = None
    app.state.generator = None
    app.state.degraded = []

    try:
        from neo4j import GraphDatabase
        app.state.neo4j_driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        )
    except Exception as exc:
        app.state.degraded.append(f"neo4j:{exc.__class__.__name__}")

    try:
        import weaviate
        app.state.weaviate_client = weaviate.Client(os.environ["WEAVIATE_URL"])
    except Exception as exc:
        app.state.degraded.append(f"weaviate:{exc.__class__.__name__}")

    try:
        import spacy
        app.state.nlp = spacy.load("en_core_web_sm")
    except Exception as exc:
        app.state.degraded.append(f"spacy:{exc.__class__.__name__}")

    try:
        from .m8_rag import load_generator
        app.state.generator = load_generator()
    except Exception as exc:
        app.state.degraded.append(f"generator:{exc.__class__.__name__}")

    if app.state.degraded:
        _logger.warning(
            "M11 backend started in DEGRADED mode (missing: %s). "
            "Live stack (docker compose up -d) is required for full behavior.",
            ", ".join(app.state.degraded),
        )

    yield

    if app.state.neo4j_driver is not None:
        try:
            app.state.neo4j_driver.close()
        except Exception:
            pass


app = FastAPI(title="M11 Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("WEB_ORIGIN", "http://localhost:3000")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# TODO (learner): wire the three middlewares onto ``app`` in the correct order.
# Starlette's ``add_middleware`` adds to the OUTSIDE of the existing chain,
# so the LAST add_middleware call is the OUTERMOST layer. You want:
#     request-id outermost, structured-logging middle, metrics innermost.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO (learner): mount /metrics on ``app`` using ``make_asgi_app()``.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Vendored M10 endpoints (do not modify).
# ---------------------------------------------------------------------------


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz")
def readyz():
    detail = {"neo4j": "unknown", "weaviate": "unknown"}
    driver = getattr(app.state, "neo4j_driver", None)
    weaviate_client = getattr(app.state, "weaviate_client", None)

    if driver is None:
        detail["neo4j"] = "not-configured"
    else:
        try:
            with driver.session() as session:
                session.run("RETURN 1").single()
            detail["neo4j"] = "ok"
        except Exception as exc:
            detail["neo4j"] = f"unavailable: {exc.__class__.__name__}"

    if weaviate_client is None:
        detail["weaviate"] = "not-configured"
    else:
        try:
            if weaviate_client.is_ready():
                detail["weaviate"] = "ok"
            else:
                detail["weaviate"] = "not ready"
        except Exception as exc:
            detail["weaviate"] = f"unavailable: {exc.__class__.__name__}"

    if detail["neo4j"] != "ok" or detail["weaviate"] != "ok":
        raise HTTPException(status_code=503, detail=detail)
    return detail


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    nlp = getattr(app.state, "nlp", None)
    if nlp is None:
        # Degraded-mode stub for CI/TestClient without spaCy.
        return ExtractResponse(entities=[])
    return ExtractResponse(entities=extract_entities(req.text, nlp))


@app.post("/kg/query", response_model=KGResponse)
def kg_query(req: KGRequest) -> KGResponse:
    driver = getattr(app.state, "neo4j_driver", None)
    if driver is None:
        # Degraded-mode stub for CI/TestClient without Neo4j.
        return KGResponse(
            cypher="MATCH (n) RETURN n LIMIT 1",
            rows=[],
            count=0,
        )
    try:
        cypher, params = wrap_kg_query(req.question)
    except UnsupportedQueryError:
        raise HTTPException(
            status_code=422,
            detail=UnsupportedQueryDetail(
                reason="unsupported_question",
                supported_patterns=list(SUPPORTED_PATTERNS),
            ).model_dump(),
        )
    with driver.session() as session:
        rows = [r.data() for r in session.run(cypher, **params)]
    return KGResponse(cypher=cypher, rows=rows, count=len(rows))


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(req: RAGRequest) -> RAGResponse:
    weaviate_client = getattr(app.state, "weaviate_client", None)
    generator = getattr(app.state, "generator", None)
    if weaviate_client is None or generator is None:
        # Degraded-mode stub for CI/TestClient without Weaviate + generator.
        return RAGResponse(
            answer="I cannot answer this from the available sources",
            citations=[],
            confidence=0.0,
            retrieved=[],
        )
    result = compose_rag(req.question, weaviate_client, generator, k=req.k)
    return RAGResponse(**result)
