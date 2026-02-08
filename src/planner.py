import yaml
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

class Planner:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cycles = self._load_cycles()
        self.state = self._load_state()
    
    def _load_cycles(self) -> dict:
        with open(self.data_dir / "cycles.yaml", 'r') as f:
            return yaml.safe_load(f)
    
    def _load_state(self) -> dict:
        state_path = self.data_dir / "state.json"
        if state_path.exists():
            with open(state_path, 'r') as f:
                return json.load(f)
        # Default state: start at week 1
        return {"current_week": 1, "last_run": None}
    
    def _save_state(self):
        with open(self.data_dir / "state.json", 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_week_template(self, week_num: int) -> Dict:
        """Get the raw cycle template for a given week (1-9)."""
        for cycle in self.cycles['cycles']:
            if cycle['week'] == week_num:
                return cycle['days']
        return {}
    
    def get_draft_plan(self, week_num: Optional[int] = None) -> Dict:
        """
        Generate a draft weekly plan.
        If week_num is not provided, use the current week from state.
        """
        if week_num is None:
            week_num = self.state['current_week']
        
        template = self.get_week_template(week_num)
        
        # For now, just return the template as-is
        # Future: resolve "Leftovers" logic, check calendar conflicts
        return {
            "week_number": week_num,
            "generated_at": datetime.now().isoformat(),
            "days": template
        }
    
    def advance_week(self):
        """Move to the next week in the 7-week cycle."""
        self.state['current_week'] = (self.state['current_week'] % 7) + 1
        self.state['last_run'] = datetime.now().isoformat()
        self._save_state()
    
    def get_available_recipes(self) -> list:
        """List all available recipe titles (parsed from frontmatter)."""
        recipes_dir = self.data_dir.parent / "_projects"
        titles = []
        for f in recipes_dir.glob("*.md"):
            try:
                with open(f, 'r') as file:
                    content = file.read()
                    # Simple frontmatter title parser to avoid heavy imports if possible
                    # but we already have models.py
                    from src.models import Recipe
                    recipe = Recipe.from_markdown(content)
                    titles.append(recipe.title)
            except Exception:
                titles.append(f.stem)
        return titles

    def get_recipe_path_by_title(self, title: str) -> Optional[Path]:
        """Find the filename for a given recipe title."""
        recipes_dir = self.data_dir.parent / "_projects"
        for f in recipes_dir.glob("*.md"):
            try:
                with open(f, 'r') as file:
                    from src.models import Recipe
                    recipe = Recipe.from_markdown(file.read())
                    if recipe.title == title:
                        return f
            except Exception:
                if f.stem == title:
                    return f
        return None

    def is_status_meal(self, meal_name: str) -> bool:
        """Check if a meal is a status placeholder (Relish, Quick-Bake, Dining Out)."""
        status_meals = ["Relish", "Quick-Bake", "Dining Out"]
        return meal_name in status_meals

    def save_plan(self, plan: Dict, filename: str = None):
        """Save a finalized plan to the plans directory."""
        plans_dir = self.data_dir / "plans"
        plans_dir.mkdir(exist_ok=True)
        
        if filename is None:
            filename = f"plan_{datetime.now().strftime('%Y-%m-%d')}.yaml"
        
        with open(plans_dir / filename, 'w') as f:
            yaml.dump(plan, f, sort_keys=False)


if __name__ == "__main__":
    # Quick test
    repo_root = Path(__file__).parent.parent
    planner = Planner(repo_root / "data")
    
    draft = planner.get_draft_plan()
    print(f"Week {draft['week_number']} Draft Plan:")
    for day, meals in draft['days'].items():
        print(f"  {day.capitalize()}: Lunch={meals.get('lunch', '-')}, Dinner={meals.get('dinner', '-')}")
