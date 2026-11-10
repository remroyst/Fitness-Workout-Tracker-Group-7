"""Authenticated CSV exports for existing FitNut logs."""

import csv
import io

from flask import Blueprint, Response

from accounts import login_required
from db import fetch_all
from feature_utils import user_id

data_export = Blueprint("data_export", __name__)


def safe_cell(value):
    if value is None:
        return ""

    result = str(value)

    if result.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + result

    return result


EXPORTS = {
    "food": (
        """
        SELECT ee.event_datetime AS logged_at,
               mt.meal_type,
               fe.food_name, fe.quantity,
               u.unit_name,
               fe.calories, fe.protein_g,
               fe.carbs_g, fe.fat_g, fe.fiber_g
        FROM food_entries fe
        JOIN eating_events ee
          ON ee.eating_event_id = fe.eating_event_id
        JOIN meal_types mt
          ON mt.meal_type_id = ee.meal_type_id
        JOIN units_of_measure u
          ON u.unit_id = fe.unit_id
        WHERE ee.user_id = %s
        ORDER BY ee.event_datetime DESC
        """,
        [
            "logged_at", "meal_type", "food_name",
            "quantity", "unit_name", "calories",
            "protein_g", "carbs_g", "fat_g", "fiber_g",
        ],
    ),
    "activity": (
        """
        SELECT a.time_started, a.time_finished,
               t.activity_name, a.custom_activity_name,
               a.calories_burned, a.notes,
               d.distance_km, d.sets_completed,
               d.repetitions, d.intensity
        FROM activity_events a
        JOIN activity_types t
          ON t.activity_type_id = a.activity_type_id
        LEFT JOIN activity_details d
          ON d.activity_event_id = a.activity_event_id
        WHERE a.user_id = %s
        ORDER BY a.time_started DESC
        """,
        [
            "time_started", "time_finished",
            "activity_name", "custom_activity_name",
            "calories_burned", "notes",
            "distance_km", "sets_completed",
            "repetitions", "intensity",
        ],
    ),
    "sleep": (
        """
        SELECT sleep_start, sleep_end,
               sleep_quality, notes
        FROM sleep_logs
        WHERE user_id = %s
        ORDER BY sleep_start DESC
        """,
        [
            "sleep_start", "sleep_end",
            "sleep_quality", "notes",
        ],
    ),
}


@data_export.get("/export/<kind>.csv")
@login_required()
def export_csv(kind):
    if kind not in EXPORTS:
        return {"error": "Invalid export type"}, 404

    query, columns = EXPORTS[kind]
    rows = fetch_all(query, (user_id(),))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(columns)

    for row in rows:
        writer.writerow([
            safe_cell(row[column])
            for column in columns
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="fitnut-{kind}.csv"'
        },
    )