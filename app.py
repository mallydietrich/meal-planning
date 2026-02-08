import streamlit as st
import yaml
from pathlib import Path
from src.github_client import GitHubClient
from src.planner import Planner
from src.models import Recipe
import pandas as pd

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
    
    if st.button("🔄 Refresh Recipes"):
        st.cache_data.clear()
        st.rerun()

    # Load Draft Plan
    draft = st.session_state.planner.get_draft_plan()
    week_num = draft['week_number']
    
    st.subheader(f"Week {week_num} Draft")
    
    updated_days = {}
    available_recipes = st.session_state.planner.get_available_recipes()
    status_meals = ["Relish", "Quick-Bake", "Dining Out"]
    options = status_meals + sorted(available_recipes)
    
    # Display Plan
    for day, meals in draft['days'].items():
        st.markdown(f"### {day.capitalize()}")
        
        lunch = meals.get('lunch', 'Relish')
        l_idx = options.index(lunch) if lunch in options else 0
        new_lunch = st.selectbox(f"🥗 Lunch", options=options, index=l_idx, key=f"lunch_{day}")
        
        dinner = meals.get('dinner', 'Dining Out')
        d_idx = options.index(dinner) if dinner in options else 0
        new_dinner = st.selectbox(f"🥘 Dinner", options=options, index=d_idx, key=f"dinner_{day}")
            
        updated_days[day] = {"lunch": new_lunch, "dinner": new_dinner}

    if st.button("Save & Finalize Plan"):
        final_plan = {
            "week_number": week_num,
            "days": updated_days,
            "finalized_at": pd.Timestamp.now().isoformat()
        }
        
        filename = f"data/plans/2026-W{week_num:02d}.yaml"
        content = yaml.dump(final_plan, sort_keys=False)
        
        try:
            st.session_state.github_client.update_file(filename, content, f"Finalize Week {week_num} Plan")
            st.success(f"Plan saved to {filename} on GitHub!")
        except Exception as e:
            st.error(f"Failed to save plan: {e}")

with tab2:
    st.header("Recipe Metadata Fixes")
    
    recipe_titles = st.session_state.planner.get_available_recipes()
    selected_recipe_title = st.selectbox("Select Recipe to Edit", options=sorted(recipe_titles))
    
    if selected_recipe_title:
        recipe_actual_path = st.session_state.planner.get_recipe_path_by_title(selected_recipe_title)
        if recipe_actual_path:
            repo_relative_path = f"recipes/{recipe_actual_path.name}"
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
