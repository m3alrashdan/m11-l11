"""Vendored from Module 8. DO NOT MODIFY.

flan-t5-base loader. Returns a callable matching the HuggingFace
`pipeline("text2text-generation", ...)` interface — call it with the
prompt string and keyword arguments (`max_new_tokens`, `do_sample`).
"""
from typing import Optional

_cached = None


def load_generator():
    """Return the flan-t5-base text-generation pipeline (cached)."""
    global _cached
    if _cached is None:
        from transformers import pipeline

        _cached = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
        )
    return _cached
