#!/usr/bin/env bash
# Seed Neo4j with the W9B recipe fixture vendored under api/seed.cypher.
# Idempotent — the cypher file uses MERGE + IF NOT EXISTS, so re-running
# does not duplicate nodes or constraints.
# Run from the repo root: bash seed_neo4j.sh
#
# Works in two environments:
#   - Local docker-compose stack: seeds via cypher-shell inside the neo4j
#     container (docker compose exec neo4j).
#   - CI / GitHub Actions service containers (no compose stack running):
#     falls back to seeding via the neo4j Python driver against $NEO4J_URI
#     (the driver is installed from requirements.txt).
set -euo pipefail

NEO4J_PASSWORD="${NEO4J_PASSWORD:-devpassword}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
SEED_FILE="api/seed.cypher"

if [ ! -f "$SEED_FILE" ]; then
  echo "ERROR: $SEED_FILE not found. Run from the repo root." >&2
  exit 1
fi

if docker compose ps --status running 2>/dev/null | grep -qw neo4j; then
  echo "Seeding Neo4j (cypher-shell inside the compose neo4j container) ..."
  docker compose exec -T neo4j cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" < "$SEED_FILE"
else
  echo "Seeding Neo4j (neo4j Python driver against $NEO4J_URI) ..."
  NEO4J_URI="$NEO4J_URI" NEO4J_USER="$NEO4J_USER" NEO4J_PASSWORD="$NEO4J_PASSWORD" \
    SEED_FILE="$SEED_FILE" python3 - <<'PY'
import os
from neo4j import GraphDatabase

uri = os.environ["NEO4J_URI"]
auth = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])

with open(os.environ["SEED_FILE"]) as fh:
    raw = fh.read()

# Strip // line comments, then split into statements on ';'. cypher-shell
# evaluates ';'-separated statements independently; the driver runs one
# statement per session.run, so we mirror that. The fixture contains no
# string literals with ';' or '//', so this split is safe.
body = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("//"))
statements = [s.strip() for s in body.split(";") if s.strip()]

driver = GraphDatabase.driver(uri, auth=auth)
with driver.session() as session:
    for stmt in statements:
        session.run(stmt)
driver.close()
print(f"Neo4j seeded: {len(statements)} statements executed (idempotent).")
PY
fi
echo "Done."
