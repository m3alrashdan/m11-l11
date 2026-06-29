#!/usr/bin/env bash
# Seed Weaviate with the M11 Lab RAG chunk corpus (Boston restaurants).
# Idempotent — re-running skips chunk_ids already present.
# Run from the repo root: bash seed_weaviate.sh
#
# The seeder runs INSIDE the `api` container so we do not depend on the host
# venv having weaviate-client + sentence-transformers installed. This matches
# the seed_neo4j.sh pattern (cypher-shell inside the neo4j container) and
# means the only host requirement is a running Docker stack.
set -euo pipefail

echo "Seeding Weaviate via the api container ..."
docker compose exec -T \
  -e WEAVIATE_URL="${WEAVIATE_URL:-http://weaviate:8080}" \
  api python /app/api/seed_weaviate.py
echo "Done."
