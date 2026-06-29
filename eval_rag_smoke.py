"""RAG smoke evaluator -- 3 pre-shipped questions, binary PASS/FAIL per question.

The Lab smoke evaluator proves the grounding-check logic that the Integration's
RAG grounding-rate harness scales up. It is binary by design (PASS/FAIL per
question, exit 0 iff all PASS); it does not aggregate a rate, and it does NOT
apply decline-exclusion -- the three smoke questions are all answerable
against the seeded fixtures, so a decline at the Lab tier is a defect.

Grounding-check methodology (Lab smoke):

  A response is grounded iff (a) response.citations has length >= 1 AND
  (b) every chunk_id in response.citations is present in the candidate set
  returned by the retrieval call for the same question. The Lab smoke does
  NOT apply decline-exclusion (the Lab's 3 questions are all answerable
  against the seeded Weaviate; decline is not in scope at the Lab tier).

The same paragraph appears in the published Applied Lab page so the
documented methodology and the code that scores against it stay in sync.
"""

import json
import os
import sys


API_URL = os.environ.get("API_URL", "http://localhost:8000")


def score_grounding(response: dict, candidate_ids) -> bool:
    """Return True iff `response` is grounded per the Lab smoke methodology.

    `response` is the JSON body returned by POST /rag/answer.
    `candidate_ids` is the set of chunk_ids returned for the same question.
    """
    # TODO: implement per the methodology paragraph above.
    # Both conditions must hold:
    #   (a) at least one citation is present
    #   (b) every cited chunk_id is in the candidate set
    raise NotImplementedError


def evaluate_question(question: dict) -> bool:
    """Issue one POST /rag/answer; return True iff the response is grounded."""
    # TODO: POST to /rag/answer with the question + k from the fixture.
    # Use a generous timeout -- /rag/answer cold-cache can take ~10 s.
    # Read the candidate set from the response body's `retrieved` field.
    # Call score_grounding(response_body, candidate_ids).
    raise NotImplementedError


def main() -> int:
    """Iterate the three smoke questions, print PASS/FAIL, return 0 iff all PASS."""
    fixture_path = os.path.join(os.path.dirname(__file__), "data", "rag_smoke.json")
    with open(fixture_path) as fh:
        questions = json.load(fh)

    # TODO: iterate `questions`, call evaluate_question on each, print PASS or
    # FAIL per question, return 0 iff every question is grounded, else 1.
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
