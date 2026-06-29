"""Vendored M10 RAG composer (with M11 extension).

Reference material — the M11 Lab does NOT require you to modify this file.

The Lab's smoke evaluator (``eval_rag_smoke.py``) calls ``POST /rag/answer``
on the running stack, which is wired through this composer in production
runs (``docker compose up -d`` + seeded Weaviate). In CI / TestClient runs
without external services configured, ``api/main.py``'s ``/rag/answer``
returns a stub.

Grounding contract: when ``answer`` is not the empty-retrieval sentinel,
``len(citations) > 0`` is required. Every cited ``chunk_id`` corresponds to
a chunk in the top-``k`` retrieved from Weaviate. Generator called with
``do_sample=False`` for reproducibility.

M11 extension: ``compose_rag`` returns a ``retrieved`` field — the list of
candidate chunks (each a dict with ``chunk_id``) returned by the
retrieval call — so the Lab's
smoke evaluator and the Integration's grounding-rate harness can verify
every cited id is in the retrieval set without re-issuing the retrieval
query.
"""
import re
from functools import lru_cache
from typing import Tuple

EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_embedder():
    """Lazy-load the sentence-transformer used to embed RAG queries.

    The Lab's compose file runs Weaviate with ``DEFAULT_VECTORIZER_MODULE=none``,
    so queries are embedded client-side and pushed via ``with_near_vector``.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDER)


PROMPT_TEMPLATE = """\
You are answering a question. Use ONLY the numbered sources below.
Cite each claim with the source number in square brackets, e.g. [1].
If the sources do not contain the answer, say: I cannot answer this from the available sources.

Sources:
{sources}

Question: {question}
Answer:"""

SENTINEL = "I cannot answer this from the available sources"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def assemble_prompt(question: str, chunks: list) -> Tuple[str, dict]:
    """Number the retrieved chunks 1..k and substitute into the prompt template."""
    numbered = {}
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        numbered[i] = chunk
        lines.append(f"[{i}] {chunk['text']}")
    sources = "\n".join(lines)
    return PROMPT_TEMPLATE.format(sources=sources, question=question), numbered


def extract_citations(answer: str, numbered: dict) -> list:
    """Pull [N]-style markers from `answer` and resolve to retrieved chunks."""
    cited = []
    seen = set()
    for match in CITATION_PATTERN.finditer(answer):
        idx = int(match.group(1))
        if idx in numbered and idx not in seen:
            seen.add(idx)
            chunk = numbered[idx]
            cited.append({"chunk_id": chunk["chunk_id"], "score": chunk["score"]})
    return cited


def compose_rag(question: str, weaviate_client, generator, k: int = 4) -> dict:
    """Run the four-stage RAG pipeline (retrieve -> assemble -> generate -> cite).

    Returns a dict with the keys ``answer``, ``citations``, ``confidence``,
    and ``retrieved`` (list of candidate chunks, each ``{"chunk_id": ...}``).
    The M11 ``retrieved``
    field lets the Lab smoke evaluator / Integration grounding harness
    verify every cited id is in the candidate set.
    """
    query_vector = _get_embedder().encode(question).tolist()
    raw_query = (
        weaviate_client.query.get("Chunk", ["chunk_id", "text"])
        .with_near_vector({"vector": query_vector})
        .with_limit(k)
        .with_additional(["distance"])
        .do()
    )
    retrieved = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": 1.0 - c["_additional"]["distance"],
        }
        for c in raw_query["data"]["Get"]["Chunk"]
    ]
    retrieved_candidates = [{"chunk_id": r["chunk_id"]} for r in retrieved]
    if not retrieved:
        return {
            "answer": SENTINEL,
            "citations": [],
            "confidence": 0.0,
            "retrieved": retrieved_candidates,
        }

    prompt, numbered = assemble_prompt(question, retrieved)
    raw = generator(prompt, max_new_tokens=256, do_sample=False)[0]["generated_text"]
    citations = extract_citations(raw, numbered)
    if not citations:
        return {
            "answer": SENTINEL,
            "citations": [],
            "confidence": 0.0,
            "retrieved": retrieved_candidates,
        }

    confidence = sum(c["score"] for c in citations) / len(citations)
    confidence = max(0.0, min(1.0, confidence))
    return {
        "answer": raw,
        "citations": citations,
        "confidence": confidence,
        "retrieved": retrieved_candidates,
    }
