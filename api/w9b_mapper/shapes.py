"""The 15 supported question shapes the W9B mapper recognizes. DO NOT MODIFY.

Returned in the 422 detail payload when an unsupported question is
rejected. Paired with ``mapper.py``'s ``_PATTERNS`` list — the two files
are kept in sync as a single contract.
"""

SUPPORTED_PATTERNS = (
    "Find recipes that use {ingredient}",
    "Find {cuisine} recipes",
    "Find recipes by {chef}",
    "Find recipes with cooking time under {minutes} minutes",
    "Find vegetarian recipes",
    "Find vegan recipes",
    "Find gluten-free recipes",
    "Find recipes that pair with {ingredient}",
    "Find recipes from {region}",
    "Find recipes that contain {ingredient} and {ingredient}",
    "Find substitutes for {ingredient}",
    "Find recipes by difficulty {level}",
    "Find recipes for {meal_type}",
    "Find recipes ranked by rating",
    "Find recipes using {technique}",
)
