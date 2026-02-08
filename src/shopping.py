from typing import List, Dict
from src.models import Recipe, Ingredient
from src.utils import format_quantity

class ShoppingCart:
    def __init__(self):
        self.items = {} # key: (name, unit)

    def add_recipes(self, recipes: List[Recipe]):
        for recipe in recipes:
            for ing in recipe.ingredients:
                self.add_ingredient(ing)

    def add_ingredient(self, ing: Ingredient):
        # Normalize name and unit for better matching
        name_norm = ing.name.lower().strip()
        unit_norm = ing.unit.lower().strip()
        
        # Basic pluralization handle (very naive)
        if name_norm.endswith('s') and not name_norm.endswith('ss'):
             # Check if singular exists in items
             singular = name_norm[:-1]
             if (singular, unit_norm) in self.items:
                 name_norm = singular
        elif (name_norm + 's', unit_norm) in self.items:
             name_norm = name_norm + 's'

        key = (name_norm, unit_norm)
        if key not in self.items:
            self.items[key] = {
                "display_name": ing.name, # Keep one display name
                "name": name_norm,
                "unit": unit_norm,
                "quantity": 0.0,
                "food_group": ing.food_group
            }
        
        self.items[key]["quantity"] += ing.quantity

    def get_aggregated_list(self) -> List[Dict]:
        """Returns a list of dictionaries with formatted quantities."""
        result = []
        # Group by food group for better shopping experience
        sorted_keys = sorted(self.items.keys(), key=lambda x: (self.items[x]["food_group"], x[0]))
        
        for key in sorted_keys:
            data = self.items[key]
            _, unit, display_str = format_quantity(data["quantity"], data["unit"])
            
            # Combine quantity and unit
            full_qty = f"{display_str} {unit}".strip()
            
            result.append({
                "name": data["display_name"],
                "quantity": full_qty,
                "food_group": data["food_group"] or "Other"
            })
        return result

if __name__ == "__main__":
    # Simple test
    i1 = Ingredient(name="Apple", quantity=2, unit="count", food_group="Produce")
    i2 = Ingredient(name="apples", quantity=3, unit="count", food_group="Produce")
    
    cart = ShoppingCart()
    cart.add_ingredient(i1)
    cart.add_ingredient(i2)
    
    print(cart.get_aggregated_list())
