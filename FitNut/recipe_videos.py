"""UC12: Recipe video demonstrations."""

import re
from urllib.parse import urlparse, parse_qs

from flask import Blueprint, g, render_template, request

from accounts import login_required
from db import execute, fetch_all, fetch_one, get_db
from validation import payload, text

recipe_videos = Blueprint("recipe_videos", __name__)

CATEGORIES = ("breakfast", "lunch", "dinner", "snack")


def user_id():
    return g.user["user_id"]


def youtube_id(value):
    if not isinstance(value, str):
        raise ValueError("Enter a YouTube video URL")

    value = value.strip()

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    parsed = urlparse(value)

    if parsed.scheme != "https":
        raise ValueError("Use a valid HTTPS YouTube URL")

    host = (parsed.hostname or "").lower()

    video_id = None

    if host in ("youtube.com", "www.youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/")[2]

    elif host in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.strip("/")

    if not video_id or not re.fullmatch(
        r"[A-Za-z0-9_-]{11}", video_id
    ):
        raise ValueError("Enter a valid YouTube video URL")

    return video_id


def positive_int(data, key, maximum):
    value = data.get(key)

    if (
        isinstance(value, bool)
        or not isinstance(value, (str, int))
        or not re.fullmatch(r"[0-9]+", str(value))
    ):
        raise ValueError(f"Enter a valid {key.replace('_', ' ')}")

    value = int(value)

    if not 1 <= value <= maximum:
        raise ValueError(
            f"{key.replace('_', ' ').capitalize()} must "
            f"be between 1 and {maximum}"
        )

    return value


def validate_recipe(data):
    title = text(data, "title", 150)
    description = text(
        data, "description", 1000, required=False
    )
    ingredients = text(data, "ingredients", 10000)
    instructions = text(data, "instructions", 20000)

    category = data.get("category")
    if category not in CATEGORIES:
        raise ValueError("Choose a valid recipe category")

    video_id = youtube_id(data.get("video_url"))
    minutes = positive_int(data, "preparation_minutes", 1440)
    servings = positive_int(data, "servings", 100)

    return (
        title,
        description,
        ingredients,
        instructions,
        video_id,
        minutes,
        servings,
        category,
    )


def read_recipes(search="", category=""):
    search_pattern = "%" + search + "%"

    return fetch_all(
        """
        SELECT
            r.recipe_id,
            r.created_by,
            r.title,
            r.description,
            r.ingredients,
            r.instructions,
            r.youtube_video_id,
            r.preparation_minutes,
            r.servings,
            r.category,
            r.created_at,
            u.first_name,
            u.last_name,
            EXISTS (
                SELECT 1
                FROM saved_video_recipes s
                WHERE s.recipe_id = r.recipe_id
                  AND s.user_id = %s
            ) AS is_saved
        FROM video_recipes r
        JOIN users u ON u.user_id = r.created_by
        WHERE (
            %s = ''
            OR r.title LIKE %s
            OR r.ingredients LIKE %s
        )
          AND (%s = '' OR r.category = %s)
        ORDER BY r.created_at DESC, r.recipe_id DESC
        LIMIT 100
        """,
        (
            user_id(),
            search,
            search_pattern,
            search_pattern,
            category,
            category,
        ),
    )


@recipe_videos.get("/recipes")
@login_required(html=True)
def recipes_page():
    search = request.args.get("q", "").strip()[:80]
    category = request.args.get("category", "")

    if category not in ("",) + CATEGORIES:
        category = ""

    return render_template(
        "recipe_videos.html",
        recipes=read_recipes(search, category),
        search=search,
        category=category,
        categories=CATEGORIES,
        current_user_id=user_id(),
    )


@recipe_videos.post("/recipes")
@login_required()
def create_recipe():
    values = validate_recipe(payload())

    execute(
        """
        INSERT INTO video_recipes (
            created_by, title, description,
            ingredients, instructions,
            youtube_video_id,
            preparation_minutes, servings, category
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id(),) + values,
    )

    get_db().commit()

    return {"message": "Recipe video added."}, 201


@recipe_videos.put("/recipes/<int:recipe_id>")
@login_required()
def update_recipe(recipe_id):
    values = validate_recipe(payload())

    _, changed = execute(
        """
        UPDATE video_recipes
        SET title = %s,
            description = %s,
            ingredients = %s,
            instructions = %s,
            youtube_video_id = %s,
            preparation_minutes = %s,
            servings = %s,
            category = %s
        WHERE recipe_id = %s
          AND created_by = %s
        """,
        values + (recipe_id, user_id()),
    )

    if not changed:
        row = fetch_one(
            """
            SELECT recipe_id FROM video_recipes
            WHERE recipe_id = %s AND created_by = %s
            """,
            (recipe_id, user_id()),
        )
        if not row:
            return {"error": "Recipe not found"}, 404

    get_db().commit()

    return {"message": "Recipe updated."}


@recipe_videos.delete("/recipes/<int:recipe_id>")
@login_required()
def delete_recipe(recipe_id):
    _, changed = execute(
        """
        DELETE FROM video_recipes
        WHERE recipe_id = %s AND created_by = %s
        """,
        (recipe_id, user_id()),
    )

    if not changed:
        return {"error": "Recipe not found"}, 404

    get_db().commit()

    return {"message": "Recipe deleted."}


@recipe_videos.post("/recipes/<int:recipe_id>/save")
@login_required()
def save_recipe(recipe_id):
    recipe = fetch_one(
        "SELECT recipe_id FROM video_recipes WHERE recipe_id = %s",
        (recipe_id,),
    )

    if not recipe:
        return {"error": "Recipe not found"}, 404

    execute(
        """
        INSERT IGNORE INTO saved_video_recipes
            (user_id, recipe_id)
        VALUES (%s, %s)
        """,
        (user_id(), recipe_id),
    )

    get_db().commit()

    return {"message": "Recipe saved."}


@recipe_videos.delete("/recipes/<int:recipe_id>/save")
@login_required()
def unsave_recipe(recipe_id):
    execute(
        """
        DELETE FROM saved_video_recipes
        WHERE user_id = %s AND recipe_id = %s
        """,
        (user_id(), recipe_id),
    )

    get_db().commit()

    return {"message": "Recipe removed from saved list."}


@recipe_videos.get("/recipes/saved")
@login_required(html=True)
def saved_recipes_page():
    recipes = fetch_all(
        """
        SELECT r.recipe_id, r.title, r.category,
               r.youtube_video_id, r.preparation_minutes
        FROM saved_video_recipes s
        JOIN video_recipes r ON r.recipe_id = s.recipe_id
        WHERE s.user_id = %s
        ORDER BY s.saved_at DESC
        """,
        (user_id(),),
    )

    return render_template(
        "saved_recipes.html",
        recipes=recipes,
    )