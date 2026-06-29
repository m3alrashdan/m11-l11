"""spaCy-backed entity extraction.

The spaCy pipeline is constructed once in `main.lifespan` and resolved
via `Depends(get_nlp)`.
"""
from .models import Entity


def extract_entities(text: str, nlp) -> list[Entity]:
    """Run spaCy NER on `text` and return entities ordered by `start`."""
    doc = nlp(text)
    ents = [
        Entity(text=e.text, label=e.label_, start=e.start_char, end=e.end_char)
        for e in doc.ents
    ]
    ents.sort(key=lambda e: e.start)
    return ents
