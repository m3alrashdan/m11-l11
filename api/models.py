"""Vendored M10 Pydantic request/response models (with M11 extension).

Reference material — the M11 Lab does NOT require you to modify this file.

M11 extension: ``RAGResponse`` exposes a ``retrieved`` field — the list of
candidate chunks (each a ``RetrievedChunk`` with ``chunk_id``) returned by
the retrieval call. The Lab's smoke
evaluator and the Integration's RAG grounding-rate harness both read this
field to verify that every cited ``chunk_id`` is in the candidate set. M10
did not expose ``retrieved`` because the M10 contract scored RAG only on
``citations`` shape; the M11 contract upgrades the grounding check to
"every cited id is in the retrieval candidate set," which requires the
candidate set to be visible to the caller.

Mirrors ``web/lib/types.ts`` field-for-field — ``chunk_id`` not ``chunkId``,
``start`` not ``start_char``. Drift produces silent render failures in the
Next.js frontend.
"""
from typing import List, Literal

from pydantic import BaseModel, Field


# --- /extract --------------------------------------------------------

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class ExtractResponse(BaseModel):
    entities: List[Entity]


# --- /kg/query -------------------------------------------------------

class KGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class KGResponse(BaseModel):
    cypher: str
    rows: List[dict]
    count: int


class UnsupportedQueryDetail(BaseModel):
    reason: Literal["unsupported_question"]
    supported_patterns: List[str]


# --- /rag/answer -----------------------------------------------------

class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    k: int = Field(4, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: int
    score: float


class RetrievedChunk(BaseModel):
    chunk_id: int


class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float
    # M11 extension: candidate chunks returned by retrieval (used by the
    # Lab smoke evaluator + Integration grounding-rate harness to verify
    # every cited chunk_id is present in the retrieval set).
    retrieved: List[RetrievedChunk] = Field(default_factory=list)


# --- Health / readiness ---------------------------------------------

class HealthResponse(BaseModel):
    status: str


class ReadyDetail(BaseModel):
    neo4j: str
    weaviate: str
