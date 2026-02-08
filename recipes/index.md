---
layout: default
title: Recipes
permalink: /recipes/
---

<h1>📖 Recipe Collection</h1>

<div class="recipe-grid">
  {% assign sorted_recipes = site.recipes | sort: "title" %}
  {% for recipe in sorted_recipes %}
    <div class="recipe-card">
      <h3><a href="{{ recipe.url }}">{{ recipe.title }}</a></h3>
      <p class="recipe-meta">
        {{ recipe.cuisine }} {% if recipe.protein_type %}• {{ recipe.protein_type }}{% endif %}
      </p>
    </div>
  {% endfor %}
</div>

<style>
  .recipe-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 2em; }
  .recipe-card { border: 1px solid #eee; padding: 15px; border-radius: 8px; background: #fff; }
  .recipe-card h3 { margin-top: 0; font-size: 1.2em; }
  .recipe-meta { color: #666; font-size: 0.9em; margin-bottom: 0; }
</style>
