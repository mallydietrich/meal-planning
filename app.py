import streamlit as st
import yaml
from pathlib import Path
from datetime import datetime
from src.github_client import GitHubClient
from src.planner import Planner
from src.models import Recipe
from src.shopping import ShoppingCart

# Page Config
st.set_page_config(page_title="The Meal Engine", page_icon="🥗", layout="wide")

# Initialize Session State
if 'github_client' not in st.session_state:
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["GITHUB_REPO"]
        st.session_state.github_client = GitHubClient(token, repo_name)
    except Exception as e:
        st.error(f"Failed to initialize GitHub client: {e}. Check your secrets.toml.")

if 'planner' not in st.session_state:
    repo_root = Path(__file__).parent
    st.session_state.planner = Planner(repo_root / "data")

st.title("👩‍🍳 The Meal Engine")

tab1, tab2 = st.tabs(["📅 Plan View", "🍳 Recipe Fixes"])

with tab1:
    st.header("Weekly Plan Review")

    col1, col2 = st.columns([3, 1])
    with col1:
        week_num = st.number_input(
            "Week",
            min_value=1,
            max_value=8,
            value=st.session_state.planner.state['current_week'],
            step=1,
        )
    with col2:
        if st.button("🔄 Refresh Recipes"):
            st.cache_data.clear()
            st.rerun()

    # Load Draft Plan for selected week
    draft = st.session_state.planner.get_draft_plan(week_num=week_num)

    updated_days = {}
    available_recipes = st.session_state.planner.get_available_recipes()
    status_meals = ["Relish", "Quick-Bake", "Dining Out"]
    options = status_meals + sorted(available_recipes)

    # Display Plan
    for day, meals in draft['days'].items():
        st.markdown(f"### {day.capitalize()}")

        lunch = meals.get('lunch', 'Relish')
        l_idx = options.index(lunch) if lunch in options else 0
        new_lunch = st.selectbox(f"🥗 Lunch", options=options, index=l_idx, key=f"w{week_num}_lunch_{day}")

        dinner = meals.get('dinner', 'Dining Out')
        d_idx = options.index(dinner) if dinner in options else 0
        new_dinner = st.selectbox(f"🥘 Dinner", options=options, index=d_idx, key=f"w{week_num}_dinner_{day}")

        updated_days[day] = {"lunch": new_lunch, "dinner": new_dinner}

    if st.button("Save & Finalize Plan"):
        finalized_at = datetime.now().isoformat()
        final_plan = {
            "week_number": week_num,
            "days": updated_days,
            "finalized_at": finalized_at,
        }

        plan_filename = f"data/plans/2026-W{week_num:02d}.yaml"
        plan_content = yaml.dump(final_plan, sort_keys=False)

        try:
            # 1. Save plan YAML
            st.session_state.github_client.update_file(
                plan_filename, plan_content, f"Finalize Week {week_num} Plan"
            )

            # 2. Generate Jekyll post for _news/
            dt = datetime.fromisoformat(finalized_at)
            date_str = dt.strftime("%Y-%m-%d")
            post_name = f"_news/{date_str}-week-{week_num}-plan.md"

            # Build schedule table
            day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            plan_table = "| Day | Lunch | Dinner |\n| :--- | :--- | :--- |\n"
            for day in day_order:
                meals = updated_days.get(day, {})
                lunch_title = meals.get("lunch", "-")
                dinner_title = meals.get("dinner", "-")
                plan_table += f"| **{day.capitalize()}** | {lunch_title} | {dinner_title} |\n"

            # Build grocery list
            cart = ShoppingCart()
            repo_root = Path(__file__).parent
            for day in day_order:
                meals = updated_days.get(day, {})
                for title in [meals.get("lunch", "-"), meals.get("dinner", "-")]:
                    if title not in ["Relish", "Quick-Bake", "Dining Out", "-"]:
                        recipe_path = st.session_state.planner.get_recipe_path_by_title(title)
                        if recipe_path:
                            with open(recipe_path, "r") as f:
                                recipe = Recipe.from_markdown(f.read())
                            for ing in recipe.ingredients:
                                cart.add_ingredient(ing)

            shopping_list = cart.get_aggregated_list()
            grocery_md = "## 🛒 Grocery List\n\n"
            for item in shopping_list:
                grocery_md += f"- [ ] {item['quantity']} **{item['name']}**\n"

            # Build post content
            frontmatter = yaml.dump({
                "layout": "post",
                "title": f"Meal Plan: Week {week_num}",
                "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": False,
                "related_posts": False,
            }, sort_keys=False)

            post_content = f"---\n{frontmatter}---\n\n## 📅 Weekly Schedule\n\n{plan_table}\n{grocery_md}"

            # 3. Push the post to GitHub
            st.session_state.github_client.update_file(
                post_name, post_content, f"Publish Week {week_num} meal plan post"
            )

            st.success(f"Plan finalized and published! Saved to `{plan_filename}` and `{post_name}`.")
            st.balloons()

        except Exception as e:
            st.error(f"Failed to save plan: {e}")

with tab2:
    st.header("Recipe Metadata Fixes")

    recipe_titles = st.session_state.planner.get_available_recipes()
    selected_recipe_title = st.selectbox("Select Recipe to Edit", options=sorted(recipe_titles))

    if selected_recipe_title:
        recipe_actual_path = st.session_state.planner.get_recipe_path_by_title(selected_recipe_title)
        if recipe_actual_path:
            repo_relative_path = f"_projects/{recipe_actual_path.name}"
            try:
                raw_content = st.session_state.github_client.get_file_content(repo_relative_path)
                recipe = Recipe.from_markdown(raw_content)

                with st.form("edit_recipe"):
                    title = st.text_input("Title", value=recipe.title)
                    source = st.text_input("Source", value=recipe.source)
                    cuisine = st.text_input("Cuisine", value=recipe.cuisine)
                    protein = st.text_input("Protein Type", value=recipe.protein_type)
                    tags = st.text_input("Tags (comma separated)", value=", ".join(recipe.tags))

                    if st.form_submit_button("Update Recipe"):
                        recipe.title = title
                        recipe.source = source
                        recipe.cuisine = cuisine
                        recipe.protein_type = protein
                        recipe.tags = [t.strip() for t in tags.split(",") if t.strip()]

                        new_markdown = recipe.to_markdown()
                        st.session_state.github_client.update_file(repo_relative_path, new_markdown, f"Update metadata for {recipe.title}")
                        st.success(f"Updated {recipe.title} on GitHub!")
            except Exception as e:
                st.error(f"Error loading recipe: {e}")
        else:
            st.error(f"Could not find file for recipe: {selected_recipe_title}")
