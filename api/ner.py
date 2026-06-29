"""Backward-compatible re-export of the spaCy-backed NER wrapper.

The canonical M10 module is ``api/nlp.py``. ``api/ner.py`` is kept as a
re-export for documentation and import-path stability — the lab spec and
README reference ``api/ner.py``, and existing learner workflows may import
from this path. New code should import from ``api.nlp``.
"""
from .nlp import extract_entities  # noqa: F401
