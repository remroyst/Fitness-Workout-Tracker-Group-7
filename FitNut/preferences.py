"""Fitness preferences and profile settings."""

from datetime import date

from flask import Blueprint, render_template

from accounts import login_required
from db import execute, fetch_one
from feature_utils import (
    user_id,
    commit,
    clean_text,
    optional_decimal,
)
from validation import payload

preferences = Blueprint("preferences", __name__)


@preferences.get("/preferences")
@login_required(html=True)
def preferences_page():
    current = fetch_one(
        "SELECT * FROM user_preferences WHERE user_id = %s",
        (user_id(),),
    )

    return render_template(
        "preferences.html",
        preferences=current,
    )


@preferences.post("/api/preferences")
@login_required()
def save_preferences():
    data = payload()

    level = data.get("fitness_level", "beginner")
    units = data.get("unit_system", "metric")
    visibility = data.get("profile_visibility", "friends")

    if level not in ("beginner", "intermediate", "advanced"):
        raise ValueError("Invalid fitness level")

    if units not in ("metric", "imperial"):
        raise ValueError("Invalid measurement units")

    if visibility not in ("private", "friends", "public"):
        raise ValueError("Invalid visibility")

    birth = data.get("birth_date") or None

    if birth:
        try:
            parsed = date.fromisoformat(birth)
        except (TypeError, ValueError):
            raise ValueError("Invalid birth date")

        if parsed > date.today() or parsed.year < 1900:
            raise ValueError("Invalid birth date")

    height = optional_decimal(data, "height_cm", 275)

    if height is not None and height < 50:
        raise ValueError("Height must be at least 50 cm")

    execute(
        """
        INSERT INTO user_preferences (
            user_id, birth_date, height_cm, fitness_level,
            dietary_preferences, allergies, intolerances,
            unit_system, profile_visibility, bio
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            birth_date = VALUES(birth_date),
            height_cm = VALUES(height_cm),
            fitness_level = VALUES(fitness_level),
            dietary_preferences = VALUES(dietary_preferences),
            allergies = VALUES(allergies),
            intolerances = VALUES(intolerances),
            unit_system = VALUES(unit_system),
            profile_visibility = VALUES(profile_visibility),
            bio = VALUES(bio)
        """,
        (
            user_id(),
            birth,
            height,
            level,
            clean_text(data, "dietary_preferences", 500),
            clean_text(data, "allergies", 500),
            clean_text(data, "intolerances", 500),
            units,
            visibility,
            clean_text(data, "bio", 500),
        ),
    )

    commit()

    return {"message": "Preferences saved"}