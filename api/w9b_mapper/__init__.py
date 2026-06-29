"""Vendored from Module 9 Week B. DO NOT MODIFY.

Re-exports the deterministic NL→Cypher mapper and its error/shapes.
"""
from .errors import UnsupportedQueryError
from .mapper import map_question
from .shapes import SUPPORTED_PATTERNS

__all__ = ["UnsupportedQueryError", "map_question", "SUPPORTED_PATTERNS"]
