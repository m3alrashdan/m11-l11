# Vendored from the M10 stack with M11 observability deps layered on.
# Build context: repo root (parent of api/).
# In docker-compose.yml:  build: { context: ., dockerfile: api/Dockerfile }
#
# This preserves package-relative imports (api/main.py: from .deps import ...).
# Running `uvicorn api.main:app` from /app loads the `api` package; running
# `uvicorn main:app` from /app/api would break the relative imports with
# `ImportError: attempted relative import with no known parent package`.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
# Generous timeout + retries for transient PyPI mirror flakes on first-pull
# large wheels (torch, transformers, sentence-transformers, ~2GB total).
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r /app/requirements.txt
# Pin the spaCy model tarball directly. `python -m spacy download` queries
# the compatibility table and constructs a release URL; for some spaCy/pip
# combinations the resolver emits a malformed URL with an empty version
# segment. Pinning the URL bypasses the resolver. en_core_web_sm 3.7.1 is
# the compatible model for spaCy 3.7.x.
RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

COPY api/ /app/api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
