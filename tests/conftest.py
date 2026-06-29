"""Autograder conftest. Resolves imports from the repo root.

In the deployed template repo, `starter/` contents are at the repo root,
so `..` is where `api/` and `eval_rag_smoke.py` live.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
