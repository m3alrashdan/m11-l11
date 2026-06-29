"""Vendored from Module 8. DO NOT MODIFY.

Provides the flan-t5-base generator loader. The loader caches the
HuggingFace pipeline on first call; subsequent calls return the cached
instance. Construct once in `main.lifespan`.
"""
from .generator import load_generator

__all__ = ["load_generator"]
