"""Nutrition values associated with video recipes."""

from flask import Blueprint, render_template

from accounts import login_required
from db import execute, fetch_one
from feature_utils import (
    user_id,
    commit,
    optional_decimal,
)
from validation import payload

recipe_nutrition = Blueprint("recipe_nutrition", __name__)


@recipe_nutrition.get("/recipes/<int:recipe_id>/nutrition")
@login_required(html=True)
def nutrition_page(recipe_id):
    recipe = fetch_one(
        """
        SELECT recipe_id, title, servings, created_by
        FROM video_recipes
        WHERE recipe_id = %s
        """,
        (recipe_id,),
    )

    if not recipe:
        return {"error": "Recipe not found"}, 404

    nutrition = fetch_one(
        """
        SELECT calories_per_serving,
               protein_g, carbs_g, fat_g
        FROM recipe_nutrition
        WHERE recipe_id = %s
        """,
        (recipe_id,),
    )

    return render_template(
        "recipe_nutrition.html",
        recipe=recipe,
        nutrition=nutrition,
        can_edit=(recipe["created_by"] == user_id()),
    )


@recipe_nutrition.post("/api/recipes/<int:recipe_id>/nutrition")
@login_required()
def save_recipe_nutrition(recipe_id):
    recipe = fetch_one(
        """
        SELECT recipe_id
        FROM video_recipes
        WHERE recipe_id = %s AND created_by = %s
        """,
        (recipe_id, user_id()),
    )

    if not recipe:
        return {"error": "Recipe not found or not owned"}, 404

    data = payload()

    calories = optional_decimal(
        data, "calories_per_serving", 100000
    )
    protein = optional_decimal(data, "protein_g", 10000)
    carbs = optional_decimal(data, "carbs_g", 10000)
    fat = optional_decimal(data, "fat_g", 10000)

    execute(
        """
        INSERT INTO recipe_nutrition (
            recipe_id, calories_per_serving,
            protein_g, carbs_g, fat_g
        )
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            calories_per_serving = VALUES(calories_per_serving),
            protein_g = VALUES(protein_g),
            carbs_g = VALUES(carbs_g),
            fat_g = VALUES(fat_g)
        """,
        (recipe_id, calories, protein, carbs, fat),
    )

    commit()
    return {"message": "Recipe nutrition saved"}