#!/usr/bin/env bash
# Seed Weaviate with the M11 Lab RAG chunk corpus (Boston restaurants).
# Idempotent — re-running skips chunk_ids already present.
# Run from the repo root: bash seed_weaviate.sh
#
# Works in two environments:
#   - Local docker-compose stack: runs the seeder inside the api container so
#     it does not depend on the host venv having weaviate-client +
#     sentence-transformers installed.
#   - CI / GitHub Actions service containers (no api container running): falls
#     back to running the seeder on the host against $WEAVIATE_URL
#     (weaviate-client + sentence-transformers come from requirements.txt).
set -euo pipefail

WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"

if docker compose ps --status running 2>/dev/null | grep -qw api; then
  echo "Seeding Weaviate via the api container ..."
  docker compose exec -T \
    -e WEAVIATE_URL="${WEAVIATE_URL}" \
    api python /app/api/seed_weaviate.py
else
  echo "Seeding Weaviate (host seeder against $WEAVIATE_URL) ..."
  WEAVIATE_URL="$WEAVIATE_URL" python3 api/seed_weaviate.py
fi
echo "Done."
