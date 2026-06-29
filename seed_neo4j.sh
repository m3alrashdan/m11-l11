#!/usr/bin/env bash
# Seed Neo4j with the W9B recipe fixture vendored under api/seed.cypher.
# Idempotent — the cypher file uses MERGE + IF NOT EXISTS, so re-running
# does not duplicate nodes or constraints.
# Run from the repo root: bash seed_neo4j.sh
set -euo pipefail

NEO4J_PASSWORD="${NEO4J_PASSWORD:-devpassword}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
SEED_FILE="api/seed.cypher"

if [ ! -f "$SEED_FILE" ]; then
  echo "ERROR: $SEED_FILE not found. Run from the repo root." >&2
  exit 1
fi

echo "Seeding Neo4j (loading $SEED_FILE via cypher-shell inside the neo4j container) ..."
docker compose exec -T neo4j cypher-shell \
  -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SEED_FILE"
echo "Done."
