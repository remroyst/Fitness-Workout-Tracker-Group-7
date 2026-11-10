"""UC15: Personal workout records."""

from flask import Blueprint, g, render_template

from accounts import login_required
from db import fetch_all

personal_records = Blueprint("personal_records", __name__)


@personal_records.get("/records")
@login_required(html=True)
def records_page():
    user_id = g.user["user_id"]

    records = fetch_all(
        """
        SELECT
            a.activity_type_id,
            a.activity_name,

            COUNT(e.activity_event_id) AS workout_count,

            MAX(
                TIMESTAMPDIFF(
                    SECOND, e.time_started, e.time_finished
                )
            ) AS longest_seconds,

            MAX(e.calories_burned) AS highest_calories,

            SUM(
                TIMESTAMPDIFF(
                    SECOND, e.time_started, e.time_finished
                )
            ) AS total_seconds

        FROM activity_events e
        JOIN activity_types a
          ON a.activity_type_id = e.activity_type_id

        WHERE e.user_id = %s

        GROUP BY a.activity_type_id, a.activity_name
        ORDER BY a.activity_name
        """,
        (user_id,),
    )

    for record in records:
        record["longest_minutes"] = round(
            record["longest_seconds"] / 60, 1
        )
        record["total_hours"] = round(
            record["total_seconds"] / 3600, 1
        )

    longest = fetch_all(
        """
        SELECT
            a.activity_name,
            e.time_started,
            e.time_finished,
            TIMESTAMPDIFF(
                SECOND, e.time_started, e.time_finished
            ) AS duration_seconds
        FROM activity_events e
        JOIN activity_types a
          ON a.activity_type_id = e.activity_type_id
        WHERE e.user_id = %s
        ORDER BY duration_seconds DESC, e.activity_event_id DESC
        LIMIT 1
        """,
        (user_id,),
    )

    calories = fetch_all(
        """
        SELECT
            a.activity_name,
            e.time_started,
            e.calories_burned
        FROM activity_events e
        JOIN activity_types a
          ON a.activity_type_id = e.activity_type_id
        WHERE e.user_id = %s
          AND e.calories_burned IS NOT NULL
        ORDER BY e.calories_burned DESC, e.activity_event_id DESC
        LIMIT 1
        """,
        (user_id,),
    )

    return render_template(
        "personal_records.html",
        records=records,
        longest=longest[0] if longest else None,
        calories=calories[0] if calories else None,
    )