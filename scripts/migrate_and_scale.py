import os
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from models import Recipe, Ingredient
from database import FoodDatabase
from utils import format_quantity

def load_targets(path: str):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_target_servings(targets, meal_type, food_group):
    for group in targets['target_groups']:
        if food_group.lower() in [fg.lower() for fg in group['food_groups']]:
            return group['targets'].get(meal_type.lower(), 0)
    return 0

def scale_recipe(recipe: Recipe, targets, food_db: FoodDatabase):
    """
    Currently a pass-through. Scaling decisions are made manually per-recipe.
    The servings_per_person metadata is preserved for Phase 2's weekly balancing.
    """
    # Apply human-readable formatting to quantities (fractions/unit swaps)
    for ing in recipe.ingredients:
        if ing.quantity > 0:
            final_qty, final_unit, _ = format_quantity(ing.quantity, ing.unit)
            ing.quantity = final_qty
            ing.unit = final_unit
    
    return recipe

def main():
    repo_root = Path(__file__).parent.parent
    v2_recipes_dir = Path("/Users/mally/Downloads/Meal Plan v2/recipes")
    output_dir = repo_root / "_projects"
    
    targets = load_targets(repo_root / "data/database/serving_targets.yaml")
    food_db = FoodDatabase(repo_root / "data/database/food_db.csv")
    
    if not v2_recipes_dir.exists():
        print(f"Error: Legacy recipes dir not found at {v2_recipes_dir}")
        return

    for recipe_file in v2_recipes_dir.glob("*.md"):
        print(f"Processing {recipe_file.name}...")
        with open(recipe_file, 'r') as f:
            content = f.read()
            
        try:
            recipe = Recipe.from_markdown(content)
            scaled_recipe = scale_recipe(recipe, targets, food_db)
            
            # Save to new location
            with open(output_dir / recipe_file.name, 'w') as out_f:
                out_f.write(scaled_recipe.to_markdown())
        except Exception as e:
            print(f"Failed to process {recipe_file.name}: {e}")

if __name__ == "__main__":
    main()
