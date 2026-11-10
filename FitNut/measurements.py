"""UC09: Body measurement tracking."""

from datetime import date
from decimal import Decimal

from flask import Blueprint, g, render_template

from accounts import login_required
from db import execute, fetch_all, fetch_one, get_db, to_json
from validation import number, payload, text

measurements = Blueprint("measurements", __name__)

FIELDS = (
    "weight_kg",
    "waist_cm",
    "hips_cm",
    "chest_cm",
    "arm_cm",
    "thigh_cm",
    "body_fat_percent",
)


def validate_measurement(data):
    date_value = data.get("measured_on")

    try:
        if not isinstance(date_value, str):
            raise ValueError()

        measured_on = date.fromisoformat(date_value)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid measurement date")

    if measured_on > date.today():
        raise ValueError("Measurement date cannot be in the future")

    values = {}

    for field in FIELDS:
        values[field] = number(
            data,
            field,
            positive=True,
            optional=True,
            maximum="9999.99" if field != "body_fat_percent"
            else "100",
        )

    if all(value is None for value in values.values()):
        raise ValueError("Enter at least one body measurement")

    notes = text(data, "notes", 1000, required=False)

    return measured_on, values, notes


def read_measurements():
    return fetch_all(
        """
        SELECT measurement_id, measured_on,
               weight_kg, waist_cm, hips_cm,
               chest_cm, arm_cm, thigh_cm,
               body_fat_percent, notes
        FROM body_measurements
        WHERE user_id = %s
        ORDER BY measured_on DESC, measurement_id DESC
        LIMIT 100
        """,
        (g.user["user_id"],),
    )


def weight_summary():
    rows = fetch_all(
        """
        SELECT measured_on, weight_kg
        FROM body_measurements
        WHERE user_id = %s
          AND weight_kg IS NOT NULL
        ORDER BY measured_on DESC, measurement_id DESC
        LIMIT 2
        """,
        (g.user["user_id"],),
    )

    if not rows:
        return {
            "latest": None,
            "change": None,
            "date": None,
        }

    latest = rows[0]

    change = None
    if len(rows) > 1:
        change = latest["weight_kg"] - rows[1]["weight_kg"]

    return {
        "latest": latest["weight_kg"],
        "change": change,
        "date": latest["measured_on"],
    }


def owned_measurement(measurement_id):
    row = fetch_one(
        """
        SELECT measurement_id
        FROM body_measurements
        WHERE measurement_id = %s
          AND user_id = %s
        """,
        (measurement_id, g.user["user_id"]),
    )

    return row is not None


@measurements.get("/measurements")
@login_required(html=True)
def measurements_page():
    records = read_measurements()

    return render_template(
        "measurements.html",
        records=to_json(records),
        summary=weight_summary(),
        today=date.today().isoformat(),
    )


@measurements.post("/measurements")
@login_required()
def create_measurement():
    measured_on, values, notes = validate_measurement(payload())

    execute(
        """
        INSERT INTO body_measurements (
            user_id, measured_on,
            weight_kg, waist_cm, hips_cm,
            chest_cm, arm_cm, thigh_cm,
            body_fat_percent, notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            g.user["user_id"],
            measured_on,
            *(values[field] for field in FIELDS),
            notes,
        ),
    )

    get_db().commit()

    return {"message": "Body measurements saved."}, 201


@measurements.put("/measurements/<int:measurement_id>")
@login_required()
def update_measurement(measurement_id):
    if not owned_measurement(measurement_id):
        return {"error": "Measurement not found"}, 404

    measured_on, values, notes = validate_measurement(payload())

    execute(
        """
        UPDATE body_measurements
        SET measured_on = %s,
            weight_kg = %s,
            waist_cm = %s,
            hips_cm = %s,
            chest_cm = %s,
            arm_cm = %s,
            thigh_cm = %s,
            body_fat_percent = %s,
            notes = %s
        WHERE measurement_id = %s
          AND user_id = %s
        """,
        (
            measured_on,
            *(values[field] for field in FIELDS),
            notes,
            measurement_id,
            g.user["user_id"],
        ),
    )

    get_db().commit()

    return {"message": "Body measurements updated."}


@measurements.delete("/measurements/<int:measurement_id>")
@login_required()
def delete_measurement(measurement_id):
    if not owned_measurement(measurement_id):
        return {"error": "Measurement not found"}, 404

    execute(
        """
        DELETE FROM body_measurements
        WHERE measurement_id = %s
          AND user_id = %s
        """,
        (measurement_id, g.user["user_id"]),
    )

    get_db().commit()

    return {"message": "Body measurement deleted."}