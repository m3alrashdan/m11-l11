"""Process-level settings — env-var-backed.

Centralizes URL, credential, and origin reads so paths through the code
do not pepper `os.environ[...]` calls.
"""
import os


class Settings:
    """Container for the env-var-backed configuration.

    Reads at construction time. Construct once in lifespan; do not
    re-construct per request.
    """

    def __init__(self) -> None:
        self.neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
        self.neo4j_password = os.environ.get("NEO4J_PASSWORD", "")
        self.weaviate_url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
        self.web_origin = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
