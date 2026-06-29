// W9B recipe fixture — exercises all 15 mapper patterns.
//
// Single-transaction per logical group so MATCH-bound variables stay
// in scope through MERGE. `cypher-shell -f` evaluates statements
// separated by `;` independently; relationship MERGEs must therefore
// either re-MATCH endpoint nodes by label+property OR live in the same
// statement as the node creation.

// --- Constraints (independent statements) ---
CREATE CONSTRAINT recipe_id IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT region_name IF NOT EXISTS FOR (rg:Region) REQUIRE rg.name IS UNIQUE;
CREATE CONSTRAINT mealtype_name IF NOT EXISTS FOR (m:MealType) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT technique_name IF NOT EXISTS FOR (t:Technique) REQUIRE t.name IS UNIQUE;

// --- Taxonomy nodes ---
MERGE (:Cuisine {name: "Sichuan"});
MERGE (:Cuisine {name: "Italian"});
MERGE (:Cuisine {name: "Thai"});
MERGE (:Cuisine {name: "Japanese"});
MERGE (:Cuisine {name: "French"});

MERGE (:Region {name: "Tuscany"});
MERGE (:Region {name: "Sichuan Province"});
MERGE (:Region {name: "Provence"});
MERGE (:Region {name: "Hokkaido"});

MERGE (:MealType {name: "breakfast"});
MERGE (:MealType {name: "lunch"});
MERGE (:MealType {name: "dinner"});

MERGE (:Technique {name: "braising"});
MERGE (:Technique {name: "sauteing"});
MERGE (:Technique {name: "stir-frying"});
MERGE (:Technique {name: "roasting"});
MERGE (:Technique {name: "simmering"});

MERGE (:Ingredient {name: "ginger"});
MERGE (:Ingredient {name: "garlic"});
MERGE (:Ingredient {name: "soy sauce"});
MERGE (:Ingredient {name: "butter"});
MERGE (:Ingredient {name: "olive oil"});
MERGE (:Ingredient {name: "tofu"});
MERGE (:Ingredient {name: "basil"});
MERGE (:Ingredient {name: "tomato"});
MERGE (:Ingredient {name: "beef"});
MERGE (:Ingredient {name: "chicken"});
MERGE (:Ingredient {name: "shrimp"});
MERGE (:Ingredient {name: "miso"});
MERGE (:Ingredient {name: "parmesan"});
MERGE (:Ingredient {name: "eggs"});
MERGE (:Ingredient {name: "flour"});
MERGE (:Ingredient {name: "guanciale"});
MERGE (:Ingredient {name: "pancetta"});

MERGE (:Person {name: "Marcella Hazan"});
MERGE (:Person {name: "David Chang"});
MERGE (:Person {name: "Julia Child"});
MERGE (:Person {name: "Kenji Lopez-Alt"});

// --- Substitution edges ---
MATCH (a:Ingredient {name: "butter"}), (b:Ingredient {name: "olive oil"})
MERGE (a)-[:SUBSTITUTES_WITH]->(b);
MATCH (a:Ingredient {name: "guanciale"}), (b:Ingredient {name: "pancetta"})
MERGE (a)-[:SUBSTITUTES_WITH]->(b);

// --- Recipes (one statement per recipe, MATCH-bound endpoints) ---

MATCH (c:Cuisine {name: "Sichuan"}), (rg:Region {name: "Sichuan Province"}),
      (i_tofu:Ingredient {name: "tofu"}), (i_ginger:Ingredient {name: "ginger"}),
      (i_garlic:Ingredient {name: "garlic"}), (i_soy:Ingredient {name: "soy sauce"}),
      (i_beef:Ingredient {name: "beef"}),
      (p:Person {name: "David Chang"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "stir-frying"})
MERGE (r:Recipe {id: "r1"})
ON CREATE SET r.name = "Mapo Tofu", r.cook_minutes = 35, r.vegetarian = false,
              r.vegan = false, r.gluten_free = false, r.difficulty = "medium", r.rating = 4.7
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:FROM_REGION]->(rg)
MERGE (r)-[:USES]->(i_tofu)
MERGE (r)-[:USES]->(i_ginger)
MERGE (r)-[:USES]->(i_garlic)
MERGE (r)-[:USES]->(i_soy)
MERGE (r)-[:USES]->(i_beef)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t)
MERGE (r)-[:PAIRS_WITH]->(i_ginger);

MATCH (c:Cuisine {name: "Italian"}), (rg:Region {name: "Tuscany"}),
      (i_g:Ingredient {name: "guanciale"}), (i_p:Ingredient {name: "parmesan"}),
      (i_e:Ingredient {name: "eggs"}),
      (p:Person {name: "Marcella Hazan"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "sauteing"})
MERGE (r:Recipe {id: "r2"})
ON CREATE SET r.name = "Spaghetti alla Carbonara", r.cook_minutes = 25, r.vegetarian = false,
              r.vegan = false, r.gluten_free = false, r.difficulty = "easy", r.rating = 4.9
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:FROM_REGION]->(rg)
MERGE (r)-[:USES]->(i_g)
MERGE (r)-[:USES]->(i_p)
MERGE (r)-[:USES]->(i_e)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Thai"}),
      (i_s:Ingredient {name: "shrimp"}), (i_g:Ingredient {name: "garlic"}),
      (i_e:Ingredient {name: "eggs"}),
      (m:MealType {name: "dinner"}), (t:Technique {name: "stir-frying"})
MERGE (r:Recipe {id: "r3"})
ON CREATE SET r.name = "Pad Thai", r.cook_minutes = 30, r.vegetarian = false,
              r.vegan = false, r.gluten_free = true, r.difficulty = "medium", r.rating = 4.5
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_s)
MERGE (r)-[:USES]->(i_g)
MERGE (r)-[:USES]->(i_e)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Japanese"}), (rg:Region {name: "Hokkaido"}),
      (i_m:Ingredient {name: "miso"}), (i_t:Ingredient {name: "tofu"}),
      (m:MealType {name: "breakfast"}), (t:Technique {name: "simmering"})
MERGE (r:Recipe {id: "r4"})
ON CREATE SET r.name = "Miso Soup", r.cook_minutes = 15, r.vegetarian = true,
              r.vegan = true, r.gluten_free = true, r.difficulty = "easy", r.rating = 4.3
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:FROM_REGION]->(rg)
MERGE (r)-[:USES]->(i_m)
MERGE (r)-[:USES]->(i_t)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t)
MERGE (r)-[:PAIRS_WITH]->(i_t);

MATCH (c:Cuisine {name: "French"}), (rg:Region {name: "Provence"}),
      (i_t:Ingredient {name: "tomato"}), (i_o:Ingredient {name: "olive oil"}),
      (i_b:Ingredient {name: "basil"}),
      (p:Person {name: "Julia Child"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "roasting"})
MERGE (r:Recipe {id: "r5"})
ON CREATE SET r.name = "Ratatouille", r.cook_minutes = 75, r.vegetarian = true,
              r.vegan = true, r.gluten_free = true, r.difficulty = "medium", r.rating = 4.6
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:FROM_REGION]->(rg)
MERGE (r)-[:USES]->(i_t)
MERGE (r)-[:USES]->(i_o)
MERGE (r)-[:USES]->(i_b)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Italian"}),
      (i_t:Ingredient {name: "tomato"}), (i_b:Ingredient {name: "basil"}),
      (i_o:Ingredient {name: "olive oil"}),
      (m:MealType {name: "lunch"})
MERGE (r:Recipe {id: "r6"})
ON CREATE SET r.name = "Caprese Salad", r.cook_minutes = 10, r.vegetarian = true,
              r.vegan = false, r.gluten_free = true, r.difficulty = "easy", r.rating = 4.4
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_t)
MERGE (r)-[:USES]->(i_b)
MERGE (r)-[:USES]->(i_o)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:PAIRS_WITH]->(i_b);

MATCH (c:Cuisine {name: "French"}),
      (i_b:Ingredient {name: "beef"}), (i_g:Ingredient {name: "garlic"}),
      (i_bu:Ingredient {name: "butter"}),
      (p:Person {name: "Julia Child"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "braising"})
MERGE (r:Recipe {id: "r7"})
ON CREATE SET r.name = "Beef Bourguignon", r.cook_minutes = 180, r.vegetarian = false,
              r.vegan = false, r.gluten_free = false, r.difficulty = "hard", r.rating = 4.8
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_b)
MERGE (r)-[:USES]->(i_g)
MERGE (r)-[:USES]->(i_bu)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Sichuan"}),
      (i_t:Ingredient {name: "tofu"}), (i_gi:Ingredient {name: "ginger"}),
      (i_ga:Ingredient {name: "garlic"}), (i_s:Ingredient {name: "soy sauce"}),
      (p:Person {name: "Kenji Lopez-Alt"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "stir-frying"})
MERGE (r:Recipe {id: "r8"})
ON CREATE SET r.name = "Tofu Stir-Fry", r.cook_minutes = 20, r.vegetarian = true,
              r.vegan = true, r.gluten_free = false, r.difficulty = "easy", r.rating = 4.1
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_t)
MERGE (r)-[:USES]->(i_gi)
MERGE (r)-[:USES]->(i_ga)
MERGE (r)-[:USES]->(i_s)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "French"}),
      (i_e:Ingredient {name: "eggs"}), (i_b:Ingredient {name: "butter"}),
      (p:Person {name: "Julia Child"}), (m:MealType {name: "breakfast"}),
      (t:Technique {name: "sauteing"})
MERGE (r:Recipe {id: "r9"})
ON CREATE SET r.name = "French Omelette", r.cook_minutes = 8, r.vegetarian = true,
              r.vegan = false, r.gluten_free = true, r.difficulty = "medium", r.rating = 4.6
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_e)
MERGE (r)-[:USES]->(i_b)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Thai"}),
      (i_c:Ingredient {name: "chicken"}), (i_ga:Ingredient {name: "garlic"}),
      (i_gi:Ingredient {name: "ginger"}),
      (m:MealType {name: "dinner"}), (t:Technique {name: "simmering"})
MERGE (r:Recipe {id: "r10"})
ON CREATE SET r.name = "Thai Green Curry", r.cook_minutes = 40, r.vegetarian = false,
              r.vegan = false, r.gluten_free = true, r.difficulty = "medium", r.rating = 4.5
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_c)
MERGE (r)-[:USES]->(i_ga)
MERGE (r)-[:USES]->(i_gi)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);

MATCH (c:Cuisine {name: "Italian"}),
      (i_o:Ingredient {name: "olive oil"}), (i_f:Ingredient {name: "flour"}),
      (m:MealType {name: "breakfast"})
MERGE (r:Recipe {id: "r11"})
ON CREATE SET r.name = "Avocado Toast", r.cook_minutes = 5, r.vegetarian = true,
              r.vegan = true, r.gluten_free = false, r.difficulty = "easy", r.rating = 4.0
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_o)
MERGE (r)-[:USES]->(i_f)
MERGE (r)-[:FOR_MEAL]->(m);

MATCH (c:Cuisine {name: "French"}),
      (i_c:Ingredient {name: "chicken"}), (i_b:Ingredient {name: "butter"}),
      (i_g:Ingredient {name: "garlic"}),
      (p:Person {name: "Julia Child"}), (m:MealType {name: "dinner"}),
      (t:Technique {name: "roasting"})
MERGE (r:Recipe {id: "r12"})
ON CREATE SET r.name = "Roasted Chicken", r.cook_minutes = 90, r.vegetarian = false,
              r.vegan = false, r.gluten_free = true, r.difficulty = "easy", r.rating = 4.7
MERGE (r)-[:HAS_CUISINE]->(c)
MERGE (r)-[:USES]->(i_c)
MERGE (r)-[:USES]->(i_b)
MERGE (r)-[:USES]->(i_g)
MERGE (r)-[:AUTHORED_BY]->(p)
MERGE (r)-[:FOR_MEAL]->(m)
MERGE (r)-[:USES_TECHNIQUE]->(t);
