import yaml
from typing import List, Optional, Dict
from dataclasses import dataclass, field

@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str
    food_group: str
    servings_per_person: float = 0.0
    extra_data: Dict = field(default_factory=dict)
    
    def __init__(self, **kwargs):
        # Mandatory fields
        self.name = kwargs.pop('name')
        
        # Handle fractional strings like '1/2'
        qty_raw = kwargs.pop('quantity', 0.0)
        if isinstance(qty_raw, str) and '/' in qty_raw:
            try:
                num, den = qty_raw.split('/')
                self.quantity = float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                self.quantity = 0.0
        else:
            try:
                self.quantity = float(qty_raw)
            except (ValueError, TypeError):
                self.quantity = 0.0
                
        self.unit = kwargs.pop('unit', '')
        self.food_group = kwargs.pop('food_group', '')
        
        try:
            self.servings_per_person = float(kwargs.pop('servings_per_person', 0.0))
        except (ValueError, TypeError):
            self.servings_per_person = 0.0
            
        # Catch everything else
        self.extra_data = kwargs

    def to_dict(self):
        from utils import format_quantity
        _, _, display_qty = format_quantity(self.quantity, self.unit)
        
        data = {
            "name": self.name,
            "quantity": display_qty.split(' ')[0], # Just the number part
            "unit": self.unit,
            "food_group": self.food_group,
            "servings_per_person": self.servings_per_person
        }
        data.update(self.extra_data)
        return data

@dataclass
class Recipe:
    title: str
    source: str = ""
    tags: List[str] = field(default_factory=list)
    cuisine: str = ""
    protein_type: str = ""
    meal_type: List[str] = field(default_factory=list)
    total_servings: int = 2
    ingredients: List[Ingredient] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)

    @classmethod
    def from_markdown(cls, content: str):
        # Basic YAML frontmatter parser
        parts = content.split('---')
        if len(parts) < 3:
            raise ValueError("Invalid markdown format: missing frontmatter")
        
        metadata = yaml.safe_load(parts[1])
        instructions_text = parts[2].strip()
        
        # Parse ingredients
        ingredients = []
        for ing_data in metadata.get('ingredients', []):
            ingredients.append(Ingredient(**ing_data))
            
        return cls(
            title=metadata.get('title', 'Untitled'),
            source=metadata.get('source', ''),
            tags=metadata.get('tags', []),
            cuisine=metadata.get('cuisine', ''),
            protein_type=metadata.get('protein_type', ''),
            meal_type=metadata.get('meal_type', []),
            total_servings=metadata.get('total_servings', 2),
            ingredients=ingredients,
            instructions=instructions_text.split('\n'),
        )

    def to_markdown(self) -> str:
        metadata = {
            "title": self.title,
            "source": self.source,
            "tags": self.tags,
            "cuisine": self.cuisine,
            "protein_type": self.protein_type,
            "meal_type": self.meal_type,
            "total_servings": self.total_servings,
            "ingredients": [i.to_dict() for i in self.ingredients],
        }
        
        frontmatter = yaml.dump(metadata, sort_keys=False)
        
        # Filter out tip blocks from instructions
        clean_instructions = []
        in_tip_block = False
        for line in self.instructions:
            if line.strip().startswith('> [!tip]'):
                in_tip_block = True
                continue
            if in_tip_block and line.strip().startswith('>'):
                continue
            in_tip_block = False
            clean_instructions.append(line)
        
        instructions = "\n".join(clean_instructions)
        
        return f"---\n{frontmatter}---\n\n{instructions}"
