"""Autograder: RAG smoke evaluator grounding-check logic.

Maps to test plan rows:
  - test_smoke_evaluator_exits_zero  (live; verified in CI against the seeded stack)
  - test_smoke_evaluator_catches_ungrounded  (unit; injects synthetic response)

The exit-zero test runs in CI where docker-compose is up. Locally we exercise
the scoring helper against synthetic fixtures.
"""
import os
import sys

import pytest

from eval_rag_smoke import score_grounding


def test_smoke_evaluator_catches_ungrounded():
    """`score_grounding` returns False when citations are empty.

    Catches buggy variant: grounding-check accepts no-citation responses.
    """
    response = {"answer": "x", "citations": []}
    candidate_ids = {"chunk-1", "chunk-2"}
    result = score_grounding(response, candidate_ids)
    assert result is False, (
        "score_grounding({citations: []}, ...) returned True; expected False. "
        "The grounding-check methodology requires citations have length >= 1."
    )


def test_smoke_evaluator_catches_unresolved_citation():
    """`score_grounding` returns False when a citation chunk_id is not in candidates.

    Catches buggy variant: grounding-check accepts dangling citations.
    """
    response = {"answer": "x", "citations": [{"chunk_id": "ghost"}]}
    candidate_ids = {"chunk-1", "chunk-2"}
    result = score_grounding(response, candidate_ids)
    assert result is False, (
        "score_grounding accepted a citation whose chunk_id is not in the "
        "candidate set. The methodology requires every cited chunk_id to be "
        "in the retrieval candidate set."
    )


def test_smoke_evaluator_accepts_grounded():
    """`score_grounding` returns True when citations are present and resolve.

    Catches buggy variant: grounding-check is too strict (false negatives).
    """
    response = {"answer": "x", "citations": [{"chunk_id": "chunk-1"}]}
    candidate_ids = {"chunk-1", "chunk-2"}
    result = score_grounding(response, candidate_ids)
    assert result is True, (
        "score_grounding rejected a fully grounded response. Verify both "
        "conditions: citations length >= 1 AND every cited chunk_id is in the "
        "candidate set."
    )


# ---------------------------------------------------------------------------
# Non-gated orchestration tests (monkeypatch httpx.post)
#
# These tests prove that `evaluate_question` and `main` actually call the
# /rag/answer endpoint and reduce to score_grounding -- without requiring the
# live docker-compose stack. The live-stack `test_smoke_evaluator_exits_zero`
# below remains as additional belt-and-suspenders coverage in CI; these unit
# tests are the autograder's primary gate on the orchestration logic.
# ---------------------------------------------------------------------------


class _StubResponse:
    """Minimal stand-in for httpx.Response — only what evaluate_question uses."""

    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class _StubHttpx:
    """Records the post() invocation; returns a configurable payload."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, "kwargs": kwargs})
        return _StubResponse(self.payload)


def _grounded_payload(chunk_id="chunk-1"):
    return {
        "answer": "Acme Bistro serves Italian.",
        "citations": [{"chunk_id": chunk_id}],
        "retrieved": [{"chunk_id": chunk_id}, {"chunk_id": "chunk-2"}],
    }


def _ungrounded_payload():
    return {
        "answer": "x",
        "citations": [],
        "retrieved": [{"chunk_id": "chunk-1"}],
    }


def test_evaluate_question_calls_endpoint_with_timeout(monkeypatch):
    """`evaluate_question` POSTs to /rag/answer with a `timeout=` kwarg.

    Catches buggy variant: missing timeout (httpx defaults to 5 s; /rag/answer
    cold-cache is 8-15 s, so missing timeout produces flaky errors).
    """
    import eval_rag_smoke

    stub = _StubHttpx(_grounded_payload())
    monkeypatch.setattr(eval_rag_smoke, "httpx", stub, raising=False)

    question = {"question": "What does Acme Bistro serve?", "k": 4}
    result = eval_rag_smoke.evaluate_question(question)

    assert len(stub.calls) == 1, (
        f"evaluate_question should POST exactly once; observed {len(stub.calls)} calls."
    )
    call = stub.calls[0]
    # Require the URL to be a proper http URL ending in /rag/answer -- not
    # a bare path or a hardcoded wrong host. The intent of the test is to
    # confirm the harness uses the configured API_URL base, not a hand-
    # rolled string.
    url = call["url"]
    assert url.startswith("http://") or url.startswith("https://"), (
        f"evaluate_question should POST to an http(s):// URL built from API_URL; "
        f"observed url={url!r}. Use os.environ.get('API_URL', ...) for the base."
    )
    assert url.rstrip("/").endswith("/rag/answer"), (
        f"evaluate_question should POST to .../rag/answer; observed url={url!r}."
    )
    assert "timeout" in call["kwargs"], (
        "evaluate_question must pass a `timeout=` kwarg to httpx.post."
    )
    # A timeout of 0 or a sub-second value is not a real timeout; /rag/answer
    # cold-cache is 8-15 s. Require >= 5 s so a literal `timeout=0.001`
    # placeholder does not silently pass.
    timeout_val = call["kwargs"]["timeout"]
    assert isinstance(timeout_val, (int, float)) and timeout_val >= 5, (
        f"evaluate_question's timeout must be a numeric value >= 5 s; got "
        f"{timeout_val!r}. /rag/answer cold-cache is 8-15 s; a sub-second "
        "timeout produces flaky errors."
    )
    assert result is True, (
        "evaluate_question should return score_grounding's True verdict on a "
        f"fully grounded response; returned {result!r}."
    )


def test_evaluate_question_returns_score_grounding_verdict(monkeypatch):
    """`evaluate_question` returns score_grounding's verdict (False on ungrounded).

    Catches buggy variant: evaluate_question returns the raw response, or
    always returns True, or does not call score_grounding.
    """
    import eval_rag_smoke

    stub = _StubHttpx(_ungrounded_payload())
    monkeypatch.setattr(eval_rag_smoke, "httpx", stub, raising=False)

    result = eval_rag_smoke.evaluate_question({"question": "q", "k": 4})
    assert result is False, (
        "evaluate_question should return False when score_grounding rejects "
        f"the response (no citations); returned {result!r}."
    )


def test_main_returns_zero_when_all_grounded(monkeypatch):
    """`main` returns 0 when every synthetic question is grounded.

    Catches buggy variant: main always returns 0 (silent pass) or always
    returns 1 regardless of per-question outcomes.
    """
    import eval_rag_smoke

    stub = _StubHttpx(_grounded_payload())
    monkeypatch.setattr(eval_rag_smoke, "httpx", stub, raising=False)

    exit_code = eval_rag_smoke.main()
    assert exit_code == 0, (
        f"main() should return 0 when all questions are grounded; returned {exit_code!r}."
    )


def test_main_returns_one_when_any_ungrounded(monkeypatch):
    """`main` returns 1 when at least one synthetic question is ungrounded.

    Catches buggy variant: main always returns 0 regardless of grounding.
    """
    import eval_rag_smoke

    stub = _StubHttpx(_ungrounded_payload())
    monkeypatch.setattr(eval_rag_smoke, "httpx", stub, raising=False)

    exit_code = eval_rag_smoke.main()
    assert exit_code == 1, (
        f"main() should return 1 when any question is ungrounded; returned {exit_code!r}."
    )


def test_evaluate_question_reads_candidate_set_from_retrieved(monkeypatch):
    """`evaluate_question` builds the candidate set from `retrieved`, not `citations`.

    Catches buggy variant: learner builds candidate_ids from
    `response["citations"]` -- which makes the grounding check trivially
    pass because every citation is in its own set, defeating the entire
    grounding methodology. The methodology requires the candidate set to
    be read from `response["retrieved"]` (the retrieval candidate set),
    so a citation that does NOT appear in `retrieved` must be ungrounded.

    Payload below: `citations` contains `ghost-chunk` (NOT in `retrieved`),
    so the response is ungrounded. A harness that reads candidates from
    `retrieved` correctly returns False; a harness that reads from
    `citations` would incorrectly return True.
    """
    import eval_rag_smoke

    trap_payload = {
        "answer": "Acme Bistro serves Italian.",
        "citations": [{"chunk_id": "ghost-chunk"}],
        "retrieved": [{"chunk_id": "chunk-1"}, {"chunk_id": "chunk-2"}],
    }
    stub = _StubHttpx(trap_payload)
    monkeypatch.setattr(eval_rag_smoke, "httpx", stub, raising=False)

    result = eval_rag_smoke.evaluate_question({"question": "q", "k": 4})
    assert result is False, (
        "evaluate_question returned True on a response whose only citation "
        "is not in the `retrieved` candidate set. This means the harness is "
        "building the candidate set from `citations` instead of `retrieved`. "
        "Per the methodology (reading §14), candidates come from `retrieved`."
    )


# ---------------------------------------------------------------------------
# Live-stack smoke test (gated; runs in CI only against seeded docker-compose)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("API_URL") is None or os.environ.get("M11_LIVE_STACK") != "1",
    reason="Live-stack smoke test runs in CI only (API_URL + M11_LIVE_STACK=1).",
)
def test_smoke_evaluator_exits_zero():
    """`python eval_rag_smoke.py` exits 0 on the seeded stack.

    Catches buggy variant: smoke evaluator does not call API or does not check
    grounding correctly.
    """
    import subprocess

    repo_root = os.path.join(os.path.dirname(__file__), "..")
    result = subprocess.run(
        [sys.executable, "eval_rag_smoke.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"eval_rag_smoke.py exited {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
