"""Deterministic NL→Cypher mapper for the W9B recipe domain. DO NOT MODIFY.

Covers the 15 supported question shapes enumerated in ``shapes.py``.
Returns ``(cypher: str, params: dict)`` on a match; raises
``UnsupportedQueryError`` otherwise — that rejection produces the 422
the path operation surfaces.

The recognition logic is intentionally pattern-based and rejects
anything outside the supported set. New shapes require a paired update
to ``shapes.SUPPORTED_PATTERNS`` and a regex+Cypher row here; the two
files are kept in sync as a single contract.
"""
import re

from .errors import UnsupportedQueryError

# Pattern order matters: more-specific patterns (e.g., "Find vegetarian
# recipes") must be listed before the catch-all "Find {cuisine} recipes",
# which would otherwise greedily match "vegetarian" as a cuisine name.
_PATTERNS = [
    # 1. Find recipes that use {ingredient}
    (
        re.compile(r"^find recipes that use (?P<ingredient>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:USES]->(i:Ingredient {name: $ingredient}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 12. Find recipes by difficulty {level} — must precede the chef
    #     pattern (#3) so "difficulty" is not consumed as a chef name.
    (
        re.compile(r"^find recipes by difficulty (?P<level>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE toLower(r.difficulty) = toLower($level) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 3. Find recipes by {chef} — must precede {cuisine} so "by" branch wins.
    (
        re.compile(r"^find recipes by (?P<chef>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:AUTHORED_BY]->(p:Person {name: $chef}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 4. Find recipes with cooking time under {minutes} minutes
    (
        re.compile(r"^find recipes with cooking time under (?P<minutes>\d+) minutes$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE r.cook_minutes < toInteger($minutes) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 5. Find vegetarian recipes
    (
        re.compile(r"^find vegetarian recipes$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE r.vegetarian = true "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 6. Find vegan recipes
    (
        re.compile(r"^find vegan recipes$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE r.vegan = true "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 7. Find gluten-free recipes
    (
        re.compile(r"^find gluten[- ]free recipes$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE r.gluten_free = true "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 8. Find recipes that pair with {ingredient}
    (
        re.compile(r"^find recipes that pair with (?P<ingredient>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:PAIRS_WITH]->(i:Ingredient {name: $ingredient}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 9. Find recipes from {region}
    (
        re.compile(r"^find recipes from (?P<region>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:FROM_REGION]->(reg:Region {name: $region}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 10. Find recipes that contain {ingredient_a} and {ingredient_b}
    (
        re.compile(
            r"^find recipes that contain (?P<ingredient_a>.+?) and (?P<ingredient_b>.+?)$",
            re.IGNORECASE,
        ),
        "MATCH (r:Recipe)-[:USES]->(:Ingredient {name: $ingredient_a}) "
        "MATCH (r)-[:USES]->(:Ingredient {name: $ingredient_b}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 11. Find substitutes for {ingredient}
    (
        re.compile(r"^find substitutes for (?P<ingredient>.+?)$", re.IGNORECASE),
        "MATCH (:Ingredient {name: $ingredient})-[:SUBSTITUTES_WITH]->(sub:Ingredient) "
        "RETURN sub.name AS recipe, sub.name AS id",
    ),
    # 13. Find recipes for {meal_type}
    (
        re.compile(r"^find recipes for (?P<meal_type>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:FOR_MEAL]->(m:MealType {name: $meal_type}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 14. Find recipes ranked by rating
    (
        re.compile(r"^find recipes ranked by rating$", re.IGNORECASE),
        "MATCH (r:Recipe) WHERE r.rating IS NOT NULL "
        "RETURN r.name AS recipe, r.id AS id ORDER BY r.rating DESC",
    ),
    # 15. Find recipes using {technique}
    (
        re.compile(r"^find recipes using (?P<technique>.+?)$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:USES_TECHNIQUE]->(t:Technique {name: $technique}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
    # 2. Find {cuisine} recipes — catch-all, must be last so more-specific
    #    patterns above (vegetarian, vegan, gluten-free) win first.
    (
        re.compile(r"^find (?P<cuisine>\w[\w -]+?) recipes$", re.IGNORECASE),
        "MATCH (r:Recipe)-[:HAS_CUISINE]->(c:Cuisine {name: $cuisine}) "
        "RETURN r.name AS recipe, r.id AS id",
    ),
]


def map_question(question: str):
    """Map a natural-language question to (cypher, params).

    Raises UnsupportedQueryError if no pattern matches.
    """
    q = question.strip()
    for rx, cypher in _PATTERNS:
        m = rx.match(q)
        if m:
            params = {k: v.strip() for k, v in m.groupdict().items()}
            return cypher, params
    raise UnsupportedQueryError(f"No supported pattern matched: {question!r}")
