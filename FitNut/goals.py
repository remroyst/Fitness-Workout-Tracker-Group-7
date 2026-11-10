"""UC13: Fitness and nutrition goals."""

from datetime import date, timedelta

from flask import Blueprint, g, render_template

from accounts import login_required
from db import execute, fetch_one, get_db
from validation import payload

goals = Blueprint("goals", __name__)

FITNESS_GOALS = {
    "maintain": "Maintain weight",
    "lose_weight": "Lose weight",
    "gain_muscle": "Gain muscle",
    "improve_fitness": "Improve fitness",
}


def read_goals():
    """Return the currently logged-in user's goals."""
    return fetch_one(
        """
        SELECT
            fitness_goal,
            daily_calorie_target,
            weekly_activity_minutes,
            created_at,
            updated_at
        FROM user_goals
        WHERE user_id = %s
        """,
        (g.user["user_id"],),
    )


def positive_integer(data, field, label, maximum):
    """Validate a positive whole number without silently rounding."""
    value = data.get(field)

    if isinstance(value, bool):
        raise ValueError(f"{label} must be a whole number")

    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        number = int(value)
    else:
        raise ValueError(f"{label} must be a whole number")

    if not 1 <= number <= maximum:
        raise ValueError(
            f"{label} must be between 1 and {maximum}"
        )

    return number


def goal_progress():
    """Calculate goal progress using the existing food/activity tables."""
    saved = read_goals()

    if saved is None:
        return None

    user_id = g.user["user_id"]

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)

    food = fetch_one(
        """
        SELECT
            COALESCE(SUM(f.calories), 0) AS calories,
            COUNT(f.food_entry_id) AS entries,
            COUNT(f.calories) AS calorie_entries
        FROM eating_events AS e
        JOIN food_entries AS f
            ON f.eating_event_id = e.eating_event_id
        WHERE e.user_id = %s
          AND e.event_datetime >= %s
          AND e.event_datetime < %s
        """,
        (
            user_id,
            today,
            today + timedelta(days=1),
        ),
    )

    activity = fetch_one(
        """
        SELECT
            COALESCE(
                SUM(
                    TIMESTAMPDIFF(
                        SECOND,
                        time_started,
                        time_finished
                    )
                ),
                0
            ) AS activity_seconds,
            COUNT(*) AS entries
        FROM activity_events
        WHERE user_id = %s
          AND time_started >= %s
          AND time_started < %s
        """,
        (user_id, week_start, week_end),
    )

    calories = float(food["calories"])
    calorie_target = saved["daily_calorie_target"]

    activity_minutes = round(
        float(activity["activity_seconds"]) / 60,
        1,
    )
    activity_target = saved["weekly_activity_minutes"]

    return {
        "goal": saved,
        "goal_label": FITNESS_GOALS[saved["fitness_goal"]],
        "today": today.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": (
            week_end - timedelta(days=1)
        ).isoformat(),
        "calories": calories,
        "calorie_entries": food["calorie_entries"],
        "activity_minutes": activity_minutes,
        "activity_entries": activity["entries"],
        "calorie_percent": round(
            calories / calorie_target * 100,
            1,
        ),
        "activity_percent": round(
            activity_minutes / activity_target * 100,
            1,
        ),
        "calorie_bar": min(
            100,
            round(calories / calorie_target * 100),
        ),
        "activity_bar": min(
            100,
            round(activity_minutes / activity_target * 100),
        ),
    }


@goals.get("/goals")
@login_required(html=True)
def goals_page():
    return render_template(
        "goals.html",
        saved=read_goals(),
        progress=goal_progress(),
        fitness_goals=FITNESS_GOALS,
    )


@goals.post("/goals")
@login_required()
def save_goals():
    data = payload()

    fitness_goal = data.get("fitness_goal")

    if fitness_goal not in FITNESS_GOALS:
        raise ValueError("Select a valid fitness goal")

    daily_calories = positive_integer(
        data,
        "daily_calorie_target",
        "Daily calorie target",
        20000,
    )

    weekly_minutes = positive_integer(
        data,
        "weekly_activity_minutes",
        "Weekly activity target",
        10080,
    )

    execute(
        """
        INSERT INTO user_goals (
            user_id,
            fitness_goal,
            daily_calorie_target,
            weekly_activity_minutes
        )
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            fitness_goal = VALUES(fitness_goal),
            daily_calorie_target =
                VALUES(daily_calorie_target),
            weekly_activity_minutes =
                VALUES(weekly_activity_minutes)
        """,
        (
            g.user["user_id"],
            fitness_goal,
            daily_calories,
            weekly_minutes,
        ),
    )

    get_db().commit()

    return {"message": "Your goals have been saved."}


@goals.post("/goals/clear")
@login_required()
def clear_goals():
    execute(
        "DELETE FROM user_goals WHERE user_id = %s",
        (g.user["user_id"],),
    )

    get_db().commit()

    return {"message": "Your goals have been cleared."}