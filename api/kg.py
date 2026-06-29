"""Wraps the vendored W9B deterministic NL→Cypher mapper.

The mapper itself is vendored under `w9b_mapper/` and must not be
modified.
"""
from .w9b_mapper.mapper import map_question
from .w9b_mapper.errors import UnsupportedQueryError  # re-export


def wrap_kg_query(question: str):
    """Map a natural-language question to (cypher, params).

    Raises UnsupportedQueryError if the question does not match any
    supported pattern. The path operation converts this to 422.
    """
    return map_question(question)
