"""Additional workout measurements and personal records."""

from flask import Blueprint, render_template

from accounts import login_required
from db import execute, fetch_all, fetch_one
from feature_utils import (
    user_id,
    commit,
    whole_number,
    optional_decimal,
)
from validation import payload

activity_details = Blueprint("activity_details", __name__)


@activity_details.get("/workout-details")
@login_required(html=True)
def workout_details_page():
    workouts = fetch_all(
        """
        SELECT e.activity_event_id, e.time_started,
               t.activity_name, e.custom_activity_name,
               d.distance_km, d.sets_completed,
               d.repetitions, d.intensity
        FROM activity_events e
        JOIN activity_types t
          ON t.activity_type_id = e.activity_type_id
        LEFT JOIN activity_details d
          ON d.activity_event_id = e.activity_event_id
        WHERE e.user_id = %s
        ORDER BY e.time_started DESC
        LIMIT 100
        """,
        (user_id(),),
    )

    return render_template(
        "workout_details.html",
        workouts=workouts,
    )


@activity_details.post("/api/activity/<int:event_id>/details")
@login_required()
def save_activity_details(event_id):
    event = fetch_one(
        """
        SELECT activity_event_id
        FROM activity_events
        WHERE activity_event_id = %s AND user_id = %s
        """,
        (event_id, user_id()),
    )

    if not event:
        return {"error": "Workout not found"}, 404

    data = payload()

    intensity = data.get("intensity", "moderate")

    if intensity not in ("low", "moderate", "high"):
        raise ValueError("Invalid intensity")

    distance = optional_decimal(data, "distance_km", 100000)

    sets = data.get("sets_completed")
    repetitions = data.get("repetitions")

    sets = (
        None if sets in (None, "")
        else whole_number(sets, 0, 100000)
    )

    repetitions = (
        None if repetitions in (None, "")
        else whole_number(repetitions, 0, 1000000)
    )

    execute(
        """
        INSERT INTO activity_details (
            activity_event_id, distance_km,
            sets_completed, repetitions, intensity
        )
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            distance_km = VALUES(distance_km),
            sets_completed = VALUES(sets_completed),
            repetitions = VALUES(repetitions),
            intensity = VALUES(intensity)
        """,
        (
            event_id, distance,
            sets, repetitions, intensity,
        ),
    )

    commit()
    return {"message": "Workout details saved"}


@activity_details.get("/api/records/extended")
@login_required()
def extended_records():
    rows = fetch_all(
        """
        SELECT
            e.activity_event_id,
            e.time_started,
            t.activity_name,
            d.distance_km,
            d.sets_completed,
            d.repetitions
        FROM activity_events e
        JOIN activity_types t
          ON t.activity_type_id = e.activity_type_id
        JOIN activity_details d
          ON d.activity_event_id = e.activity_event_id
        WHERE e.user_id = %s
        ORDER BY e.time_started DESC
        """,
        (user_id(),),
    )

    metrics = {
        "longest_distance": "distance_km",
        "most_sets": "sets_completed",
        "most_repetitions": "repetitions",
    }

    result = {}

    for record_name, field in metrics.items():
        eligible = [
            row for row in rows
            if row[field] is not None
        ]

        if not eligible:
            result[record_name] = None
            continue

        best = max(eligible, key=lambda row: row[field])

        result[record_name] = {
            "value": float(best[field]),
            "activity": best["activity_name"],
            "date": best["time_started"].isoformat(),
        }

    return result