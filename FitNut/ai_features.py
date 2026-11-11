"""FitNut AI features: UC02, UC03, UC14."""

import json
from datetime import datetime

from flask import (
    Blueprint,
    g,
    jsonify,
    render_template,
    request,
)

from accounts import login_required
from db import fetch_one, fetch_all, execute, get_db
from ai_service import generate_ai_json, AIServiceError


ai_features = Blueprint("ai_features", __name__)


def user_id():
    return g.user["user_id"]


def get_profile():
    preferences = fetch_one(
        """
        SELECT fitness_level,
               dietary_preferences,
               allergies,
               intolerances
        FROM user_preferences
        WHERE user_id = %s
        """,
        (user_id(),),
    ) or {}

    goals = fetch_one(
        """
        SELECT fitness_goal,
               daily_calorie_target,
               weekly_activity_minutes
        FROM user_goals
        WHERE user_id = %s
        """,
        (user_id(),),
    ) or {}

    return {
        "preferences": preferences,
        "goals": goals,
    }


def get_recent_foods():
    return fetch_all(
        """
        SELECT f.food_name,
               f.calories,
               f.protein_g,
               f.carbs_g,
               f.fat_g
        FROM food_entries AS f
        JOIN eating_events AS e
          ON e.eating_event_id = f.eating_event_id
        WHERE e.user_id = %s
        ORDER BY e.eating_event_id DESC
        LIMIT 30
        """,
        (user_id(),),
    )


def get_request_data():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        raise ValueError("Invalid request data.")

    return data


def get_text(data, field, default="", max_length=500):
    value = data.get(field, default)

    if not isinstance(value, str):
        raise ValueError(f"Invalid {field}.")

    value = value.strip()

    if len(value) > max_length:
        raise ValueError(f"{field} is too long.")

    return value


def get_number(data, field, default, minimum, maximum):
    try:
        value = int(data.get(field, default))
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field}.")

    if not minimum <= value <= maximum:
        raise ValueError(
            f"{field} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def validate_result(feature, content):
    if not isinstance(content, dict):
        raise ValueError("Invalid AI result.")

    if len(json.dumps(content)) > 150000:
        raise ValueError("AI result is too large.")

    key = (
        "suggestions"
        if feature == "nutrition"
        else "days"
    )

    items = content.get(key)

    if not isinstance(items, list) or not items:
        raise ValueError(
            "Gemini returned an incomplete result. "
            "Please generate again."
        )

    if feature == "meal":
        for day in items:
            if not isinstance(day, dict):
                raise ValueError("Invalid meal plan.")
            if not isinstance(day.get("meals"), list):
                raise ValueError("Invalid meal list.")

    elif feature == "workout":
        for day in items:
            if not isinstance(day, dict):
                raise ValueError("Invalid workout plan.")
            if not isinstance(day.get("exercises"), list):
                raise ValueError("Invalid exercise list.")

    return content


def save_result(feature, content):
    title = str(
        content.get("title", "AI Generated Plan")
    )[:160]

    generation_id, _ = execute(
        """
        INSERT INTO ai_generations
            (user_id, feature, title, content_json)
        VALUES (%s, %s, %s, %s)
        """,
        (
            user_id(),
            feature,
            title,
            json.dumps(content),
        ),
    )

    get_db().commit()
    return generation_id


def generation_count_today():
    row = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM ai_generations
        WHERE user_id = %s
          AND created_at >= UTC_DATE()
        """,
        (user_id(),),
    )

    return row["total"] if row else 0


def check_limit():
    if generation_count_today() >= 20:
        raise ValueError(
            "You have reached today's AI generation limit."
        )


@ai_features.get("/ai/<feature>")
@login_required(html=True)
def ai_page(feature):
    if feature not in (
        "meal", "workout", "nutrition"
    ):
        return "AI feature not found", 404

    titles = {
        "meal": "AI Meal Planner",
        "workout": "AI Workout Planner",
        "nutrition": "AI Nutrition Recommendations",
    }

    saved = fetch_all(
        """
        SELECT generation_id, title, status, created_at
        FROM ai_generations
        WHERE user_id = %s
          AND feature = %s
        ORDER BY generation_id DESC
        LIMIT 30
        """,
        (user_id(), feature),
    )

    return render_template(
        "ai_planner.html",
        feature=feature,
        title=titles[feature],
        profile=get_profile(),
        saved=saved,
    )


@ai_features.post("/api/ai/meal/generate")
@login_required()
def generate_meal():
    check_limit()

    data = get_request_data()
    profile = get_profile()

    goal = get_text(
        data, "goal", "maintain", 100
    )

    diet = get_text(
        data, "diet", "balanced", 200
    )

    restrictions = get_text(
        data, "restrictions", "", 500
    )

    calories = get_number(
        data, "calorie_target", 2000, 800, 6000
    )

    meals = get_number(
        data, "meals_per_day", 3, 2, 6
    )

    days = get_number(
        data, "duration_days", 1, 1, 7
    )

    if days not in (1, 7):
        raise ValueError(
            "Choose either 1 or 7 days."
        )

    structure = {
        "title": "Personalized meal plan",
        "days": [
            {
                "day": 1,
                "meals": [
                    {
                        "meal_type": "breakfast",
                        "name": "Oatmeal with fruit",
                        "ingredients": [
                            "oats",
                            "banana"
                        ],
                        "portion": "1 bowl",
                        "calories": 350,
                        "protein_g": 12,
                        "carbs_g": 55,
                        "fat_g": 8,
                        "instructions": "Preparation steps"
                    }
                ],
                "daily_calories": 2000,
                "daily_protein_g": 120,
                "daily_carbs_g": 220,
                "daily_fat_g": 65
            }
        ],
        "notes": "General meal planning guidance"
    }

    result = generate_ai_json(
        (
            f"Create exactly {days} days of meal plans "
            f"with {meals} meals per day. "
            "Include estimated calories and macros. "
            "Respect all allergies, intolerances, "
            "dietary preferences and restrictions. "
            "Provide preparation instructions."
        ),
        {
            "profile": profile,
            "goal": goal,
            "diet": diet,
            "restrictions": restrictions,
            "daily_calories": calories,
            "meals_per_day": meals,
            "duration_days": days,
        },
        structure,
    )

    validate_result("meal", result)

    if len(result["days"]) != days:
        raise ValueError(
            "Gemini returned the wrong number of days. "
            "Please regenerate."
        )

    generation_id = save_result("meal", result)

    return jsonify({
        "generation_id": generation_id,
        "content": result,
        "status": "draft",
    }), 201


@ai_features.post("/api/ai/workout/generate")
@login_required()
def generate_workout():
    check_limit()

    data = get_request_data()
    profile = get_profile()

    goal = get_text(
        data, "goal", "improve_fitness", 100
    )

    level = get_text(
        data, "fitness_level", "beginner", 50
    )

    equipment = get_text(
        data, "equipment", "bodyweight", 500
    )

    limitations = get_text(
        data, "limitations", "", 500
    )

    days = get_number(
        data, "days_per_week", 3, 1, 7
    )

    minutes = get_number(
        data, "session_minutes", 45, 10, 180
    )

    if level not in (
        "beginner",
        "intermediate",
        "advanced",
    ):
        raise ValueError("Invalid fitness level.")

    structure = {
        "title": "Weekly workout plan",
        "days": [
            {
                "day": "Monday",
                "focus": "Full body",
                "duration_minutes": 45,
                "warmup": "5 minutes of light movement",
                "exercises": [
                    {
                        "name": "Squats",
                        "sets": 3,
                        "reps": "10",
                        "rest_seconds": 60,
                        "equipment": "Bodyweight",
                        "instructions": "Exercise instructions"
                    }
                ],
                "cooldown": "5 minutes of stretching"
            }
        ],
        "notes": "Workout and recovery guidance"
    }

    result = generate_ai_json(
        (
            f"Create a weekly workout plan with "
            f"exactly {days} training days. "
            f"Each session should last about {minutes} "
            "minutes. Include warmups, exercises, "
            "sets, reps, rest periods and cooldowns. "
            "Respect equipment and physical limitations."
        ),
        {
            "profile": profile,
            "goal": goal,
            "fitness_level": level,
            "equipment": equipment,
            "limitations": limitations,
            "days_per_week": days,
            "session_minutes": minutes,
        },
        structure,
    )

    validate_result("workout", result)

    if len(result["days"]) != days:
        raise ValueError(
            "Gemini returned the wrong number "
            "of workout days. Please regenerate."
        )

    generation_id = save_result(
        "workout", result
    )

    return jsonify({
        "generation_id": generation_id,
        "content": result,
        "status": "draft",
    }), 201


@ai_features.post("/api/ai/nutrition/generate")
@login_required()
def generate_nutrition():
    check_limit()

    data = get_request_data()
    profile = get_profile()
    recent_foods = get_recent_foods()

    if not recent_foods:
        return jsonify({
            "error": (
                "Log some food first so Gemini can "
                "analyze your eating habits."
            )
        }), 400

    focus = get_text(
        data, "focus", "", 300
    )

    structure = {
        "title": "Nutrition recommendations",
        "summary": "Summary of recent eating habits",
        "suggestions": [
            {
                "food_name": "Greek yogurt",
                "portion": "1 cup",
                "quantity": 1,
                "unit": "cup",
                "calories": 150,
                "protein_g": 20,
                "carbs_g": 8,
                "fat_g": 4,
                "meal_type": "snack",
                "reason": "Supports protein intake"
            }
        ]
    }

    result = generate_ai_json(
        (
            "Analyze the user's recent meals and "
            "fitness goals. Suggest 3 to 5 foods "
            "with estimated portions and macros. "
            "Explain each recommendation briefly. "
            "Respect all dietary restrictions and "
            "allergies. Do not diagnose deficiencies."
        ),
        {
            "profile": profile,
            "recent_foods": recent_foods,
            "focus": focus,
        },
        structure,
    )

    validate_result("nutrition", result)

    generation_id = save_result(
        "nutrition", result
    )

    return jsonify({
        "generation_id": generation_id,
        "content": result,
        "status": "draft",
    }), 201


@ai_features.get("/api/ai/<int:generation_id>")
@login_required()
def get_generation(generation_id):
    record = fetch_one(
        """
        SELECT generation_id,
               feature,
               title,
               status,
               content_json
        FROM ai_generations
        WHERE generation_id = %s
          AND user_id = %s
        """,
        (generation_id, user_id()),
    )

    if not record:
        return jsonify({
            "error": "Plan not found."
        }), 404

    content = record["content_json"]

    if isinstance(content, str):
        content = json.loads(content)

    return jsonify({
        "generation_id": record["generation_id"],
        "feature": record["feature"],
        "title": record["title"],
        "status": record["status"],
        "content": content,
    })


@ai_features.put("/api/ai/<int:generation_id>")
@login_required()
def update_generation(generation_id):
    record = fetch_one(
        """
        SELECT feature
        FROM ai_generations
        WHERE generation_id = %s
          AND user_id = %s
        """,
        (generation_id, user_id()),
    )

    if not record:
        return jsonify({
            "error": "Plan not found."
        }), 404

    data = get_request_data()
    content = data.get("content")
    status = data.get("status", "draft")

    if status not in ("draft", "accepted"):
        raise ValueError("Invalid plan status.")

    validate_result(record["feature"], content)

    title = str(
        content.get("title", "AI Plan")
    )[:160]

    execute(
        """
        UPDATE ai_generations
        SET title = %s,
            content_json = %s,
            status = %s
        WHERE generation_id = %s
          AND user_id = %s
        """,
        (
            title,
            json.dumps(content),
            status,
            generation_id,
            user_id(),
        ),
    )

    get_db().commit()

    return jsonify({
        "message": "Plan saved successfully."
    })


@ai_features.delete("/api/ai/<int:generation_id>")
@login_required()
def delete_generation(generation_id):
    _, changed = execute(
        """
        DELETE FROM ai_generations
        WHERE generation_id = %s
          AND user_id = %s
        """,
        (generation_id, user_id()),
    )

    get_db().commit()

    if not changed:
        return jsonify({
            "error": "Plan not found."
        }), 404

    return jsonify({
        "message": "Plan deleted."
    })


@ai_features.errorhandler(AIServiceError)
def ai_error(error):
    return jsonify({
        "error": str(error)
    }), 503


@ai_features.errorhandler(ValueError)
def validation_error(error):
    return jsonify({
        "error": str(error)
    }), 400

@ai_features.post("/api/ai/almond/ask")
@login_required()
def ask_almond():
    data = get_request_data()

    question = get_text(
        data,
        "question",
        "",
        1000,
    )

    if not question:
        raise ValueError(
            "Please enter a question for Almond."
        )

    profile = get_profile()

    result = generate_ai_json(
        (
            "You are Almond, FitNut's friendly AI fitness "
            "and nutrition assistant. Answer the user's "
            "question clearly and concisely. "
            "Use their saved fitness goals and preferences "
            "when relevant. Offer practical meal ideas, "
            "workout guidance and general wellness tips. "
            "Respect dietary restrictions and allergies. "
            "Do not give medical diagnoses or prescribe "
            "treatment. Never claim food is guaranteed "
            "allergen-free. Return an answer in the "
            "requested JSON structure."
        ),
        {
            "question": question,
            "profile": profile,
        },
        {
            "answer": (
                "A helpful, practical response "
                "to the user's question."
            )
        },
    )

    answer = result.get("answer")

    if not isinstance(answer, str) or not answer.strip():
        raise AIServiceError(
            "Almond could not generate an answer."
        )

    return jsonify({
        "answer": answer.strip()[:8000]
    })