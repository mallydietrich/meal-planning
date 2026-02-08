import yaml
import json
from pathlib import Path
from datetime import datetime
from src.models import Recipe
from src.shopping import ShoppingCart

def get_recipe_by_title(repo_root: Path, title: str) -> Recipe:
    recipes_dir = repo_root / "recipes"
    for f in recipes_dir.glob("*.md"):
        try:
            with open(f, 'r') as file:
                recipe = Recipe.from_markdown(file.read())
                if recipe.title == title:
                    return recipe
        except Exception:
            if f.stem == title:
                 # Fallback to filename match if parsing fails
                 return Recipe.from_markdown(open(f).read())
    return None

def prepare_jekyll_data():
    repo_root = Path(__file__).parent.parent
    plans_dir = repo_root / "data" / "plans"
    
    # al-folio target directories
    posts_dir = repo_root / "_posts"
    projects_dir = repo_root / "_projects" # We'll use projects for recipes
    posts_dir.mkdir(exist_ok=True)
    projects_dir.mkdir(exist_ok=True)

    # 1. Sync recipes to _projects (al-folio uses this for grid view)
    all_recipe_files = list((repo_root / "recipes").glob("*.md"))
    for rf in all_recipe_files:
        target = projects_dir / rf.name
        try:
            with open(rf, 'r') as f:
                content = f.read()
            # al-folio projects expect a 'category' and 'importance' sometimes
            # We'll just ensure it has layout: page or similar
            if '---' in content:
                parts = content.split('---', 2)
                meta = yaml.safe_load(parts[1])
                meta['layout'] = 'page'
                meta['importance'] = 1
                meta['category'] = meta.get('cuisine', 'Other')
                
                new_content = f"---\n{yaml.dump(meta, sort_keys=False)}---\n{parts[2]}"
                with open(target, 'w') as f:
                    f.write(new_content)
        except Exception as e:
            print(f"Error syncing recipe {rf.name}: {e}")

    # 2. Process latest plan
    plan_files = sorted(plans_dir.glob("*.yaml"))
    if not plan_files:
        print("No plans found.")
        return

    latest_plan_file = plan_files[-1]
    with open(latest_plan_file, 'r') as f:
        plan_data = yaml.safe_load(f)

    week_num = plan_data.get('week_number')
    finalized_at = plan_data.get('finalized_at', datetime.now().isoformat())
    dt = datetime.fromisoformat(finalized_at)
    date_str = dt.strftime('%Y-%m-%d')
    
    post_name = f"{date_str}-week-{week_num}-plan.md"
    post_path = posts_dir / post_name
    
    # Aggregate Shopping List
    cart = ShoppingCart()
    all_recipes_used = []
    
    # Table for plan
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    plan_table = "| Day | Lunch | Dinner |\n| :--- | :--- | :--- |\n"
    
    for day in days:
        meals = plan_data['days'].get(day, {})
        lunch_title = meals.get('lunch', '-')
        dinner_title = meals.get('dinner', '-')
        
        plan_table += f"| **{day.capitalize()}** | {lunch_title} | {dinner_title} |\n"
        
        for title in [lunch_title, dinner_title]:
            if title not in ["Relish", "Quick-Bake", "Dining Out", "-"]:
                recipe = get_recipe_by_title(repo_root, title)
                if recipe:
                    for ing in recipe.ingredients:
                        cart.add_ingredient(ing)
                    if title not in all_recipes_used:
                        all_recipes_used.append(title)

    # Grocery List
    shopping_list = cart.get_aggregated_list()
    grocery_md = "## 🛒 Grocery List\n\n"
    current_group = None
    for item in shopping_list:
        if item['food_group'] != current_group:
            current_group = item['food_group']
            grocery_md += f"\n### {current_group}\n"
        grocery_md += f"- [ ] {item['quantity']} **{item['name']}**\n"

    # Frontmatter for al-folio Post
    frontmatter = {
        "layout": "post",
        "title": f"Meal Plan: Week {week_num}",
        "date": dt.strftime('%Y-%m-%d %H:%M:%S'),
        "inline": False,
        "related_posts": False
    }
    
    with open(post_path, 'w') as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, sort_keys=False)
        f.write("---\n\n")
        f.write("## 📅 Weekly Schedule\n\n")
        f.write(plan_table)
        f.write("\n")
        f.write(grocery_md)

    print(f"Jekyll Post created: {post_path}")

    print(f"Post created: {post_path}")

if __name__ == "__main__":
    prepare_jekyll_data()
