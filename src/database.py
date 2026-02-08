import csv
from typing import Dict, Optional

class FoodDatabase:
    def __init__(self, csv_path: str):
        self.db: Dict[str, Dict] = {}
        self.load(csv_path)

    def load(self, csv_path: str):
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['Ingredient (simplified name)'].lower().strip()
                if not name:
                    continue
                
                # Handle cases where quantity might be missing (Free items)
                try:
                    qty = float(row['Serving Qty']) if row['Serving Qty'] else 1.0
                except ValueError:
                    qty = 1.0 # Default if weird string

                self.db[name] = {
                    "category": row['Category'].lower().strip(),
                    "serving_qty": qty,
                    "serving_unit": row['Serving Unit'].lower().strip(),
                    "notes": row['Notes']
                }

    def lookup(self, name: str) -> Optional[Dict]:
        name = name.lower().strip()
        return self.db.get(name)
