"""Vendored Weaviate seeder for the M11 Lab live stack. Idempotent.

Reference material — the M11 Lab does NOT require you to modify this file.

Embeds chunks with sentence-transformers (``all-MiniLM-L6-v2``) and writes
them to a ``Chunk`` class. Vectors are precomputed and pushed via
``add_data_object(..., vector=...)`` because the Lab compose file runs
Weaviate with ``DEFAULT_VECTORIZER_MODULE=none``. Re-running this script
does not duplicate entries — it skips ``chunk_id``\\ s already present.
"""
import json
import os

import weaviate
from sentence_transformers import SentenceTransformer

URL = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"

SCHEMA = {
    "class": "Chunk",
    "vectorizer": "none",
    "properties": [
        {"name": "chunk_id", "dataType": ["int"]},
        {"name": "text", "dataType": ["text"]},
    ],
}


def main() -> None:
    client = weaviate.Client(URL)
    if not client.schema.contains({"class": "Chunk"}):
        client.schema.create_class(SCHEMA)

    with open(os.path.join(os.path.dirname(__file__), "seed_chunks.json")) as f:
        chunks = json.load(f)

    existing = client.data_object.get(class_name="Chunk", limit=10000).get("objects", [])
    existing_ids = {o["properties"]["chunk_id"] for o in existing if "properties" in o}

    model = SentenceTransformer(EMBEDDER)
    inserted = 0
    with client.batch as batch:
        batch.batch_size = 50
        for chunk in chunks:
            if chunk["chunk_id"] in existing_ids:
                continue
            vector = model.encode(chunk["text"]).tolist()
            batch.add_data_object(
                data_object={"chunk_id": chunk["chunk_id"], "text": chunk["text"]},
                class_name="Chunk",
                vector=vector,
            )
            inserted += 1
    print(f"Weaviate seeded: {inserted} new chunks (idempotent).")


if __name__ == "__main__":
    main()
