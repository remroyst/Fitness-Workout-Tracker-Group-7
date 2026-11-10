"""UC10: In-app motivation and reminders."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, render_template

from accounts import login_required
from db import execute, fetch_all, fetch_one, get_db
from validation import payload

reminders = Blueprint("reminders", __name__)

TYPES = {
    "meal": "Meal",
    "workout": "Workout",
    "water": "Water",
    "weigh_in": "Weigh-in",
}

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

MESSAGES = {
    "meal": "It's time to check your food log.",
    "workout": "It's time to check your activity plan.",
    "water": "Remember to drink water.",
    "weigh_in": "It's time for your scheduled weigh-in.",
}

MOTIVATION = (
    "Small, consistent steps make a difference."
)


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_reminder(data):
    kind = data.get("reminder_type")
    frequency = data.get("frequency")
    method = data.get("notification_method")

    if kind not in TYPES:
        raise ValueError("Choose a valid reminder type")

    if frequency not in ("daily", "weekly"):
        raise ValueError("Choose daily or weekly")

    if method not in ("in_app", "browser"):
        raise ValueError("Choose a valid notification method")

    value = data.get("reminder_time")
    if not isinstance(value, str):
        raise ValueError("Enter a valid reminder time")

    try:
        reminder_time = datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValueError("Enter a valid reminder time (HH:MM)")

    weekday = None

    if frequency == "weekly":
        try:
            weekday = int(data.get("weekday"))
        except (TypeError, ValueError):
            raise ValueError("Choose a weekday")

        if weekday not in range(7):
            raise ValueError("Choose a valid weekday")

    try:
        offset = int(data.get("utc_offset_minutes"))
    except (TypeError, ValueError):
        raise ValueError("Invalid timezone offset")

    if not -840 <= offset <= 840:
        raise ValueError("Invalid timezone offset")

    motivation = data.get("motivation_enabled") in (
        True, "true", "on", "1"
    )

    enabled = data.get("enabled") in (
        True, "true", "on", "1"
    )

    return (
        kind,
        reminder_time,
        frequency,
        weekday,
        method,
        motivation,
        enabled,
        offset,
    )


def reminder_list():
    return fetch_all(
        """
        SELECT reminder_id, reminder_type, reminder_time,
               frequency, weekday, notification_method,
               motivation_enabled, enabled, utc_offset_minutes
        FROM user_reminders
        WHERE user_id = %s
        ORDER BY reminder_id DESC
        """,
        (g.user["user_id"],),
    )


def notification_list():
    return fetch_all(
        """
        SELECT n.notification_id, n.message, n.status,
               n.due_at, n.snoozed_until,
               r.reminder_type, r.notification_method
        FROM reminder_notifications n
        JOIN user_reminders r
          ON r.reminder_id = n.reminder_id
        WHERE n.user_id = %s
          AND n.status IN ('pending', 'snoozed')
        ORDER BY n.due_at DESC
        LIMIT 50
        """,
        (g.user["user_id"],),
    )


def check_due_reminders():
    """Generate notifications when the signed-in user polls."""
    now = now_utc()
    changed = False

    for reminder in reminder_list():
        if not reminder["enabled"]:
            continue

        local_now = now + timedelta(
            minutes=reminder["utc_offset_minutes"]
        )
        local_date = local_now.date()

        if (
            reminder["frequency"] == "weekly"
            and local_now.weekday() != reminder["weekday"]
        ):
            continue

        if local_now.time() < reminder["reminder_time"]:
            continue

        if reminder.get("last_due_date") == local_date:
            continue

        message = MESSAGES[reminder["reminder_type"]]

        if reminder["motivation_enabled"]:
            message += " " + MOTIVATION

        execute(
            """
            INSERT INTO reminder_notifications
                (reminder_id, user_id, message, due_at)
            VALUES (%s, %s, %s, %s)
            """,
            (
                reminder["reminder_id"],
                g.user["user_id"],
                message,
                now,
            ),
        )

        execute(
            """
            UPDATE user_reminders
            SET last_due_date = %s
            WHERE reminder_id = %s AND user_id = %s
            """,
            (
                local_date,
                reminder["reminder_id"],
                g.user["user_id"],
            ),
        )

        changed = True

    if changed:
        get_db().commit()


def reminder_id_from_path(reminder_id):
    if reminder_id <= 0:
        raise ValueError("Invalid reminder ID")

    row = fetch_one(
        """
        SELECT reminder_id
        FROM user_reminders
        WHERE reminder_id = %s AND user_id = %s
        """,
        (reminder_id, g.user["user_id"]),
    )

    if row is None:
        raise ValueError("Reminder not found")

    return reminder_id


@reminders.get("/reminders")
@login_required(html=True)
def reminders_page():
    return render_template(
        "reminders.html",
        reminders=reminder_list(),
        notifications=notification_list(),
        types=TYPES,
        days=DAYS,
    )


@reminders.post("/reminders")
@login_required()
def create_reminder():
    values = parse_reminder(payload())

    execute(
        """
        INSERT INTO user_reminders (
            user_id, reminder_type, reminder_time, frequency,
            weekday, notification_method, motivation_enabled,
            enabled, utc_offset_minutes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (g.user["user_id"],) + values,
    )

    get_db().commit()
    return {"message": "Reminder saved."}, 201


@reminders.put("/reminders/<int:reminder_id>")
@login_required()
def update_reminder(reminder_id):
    reminder_id_from_path(reminder_id)
    values = parse_reminder(payload())

    execute(
        """
        UPDATE user_reminders
        SET reminder_type = %s,
            reminder_time = %s,
            frequency = %s,
            weekday = %s,
            notification_method = %s,
            motivation_enabled = %s,
            enabled = %s,
            utc_offset_minutes = %s,
            last_due_date = NULL
        WHERE reminder_id = %s AND user_id = %s
        """,
        values + (reminder_id, g.user["user_id"]),
    )

    get_db().commit()
    return {"message": "Reminder updated."}


@reminders.delete("/reminders/<int:reminder_id>")
@login_required()
def delete_reminder(reminder_id):
    reminder_id_from_path(reminder_id)

    execute(
        """
        DELETE FROM user_reminders
        WHERE reminder_id = %s AND user_id = %s
        """,
        (reminder_id, g.user["user_id"]),
    )

    get_db().commit()
    return {"message": "Reminder deleted."}


@reminders.post("/reminders/disable-all")
@login_required()
def disable_all():
    execute(
        """
        UPDATE user_reminders
        SET enabled = FALSE, motivation_enabled = FALSE
        WHERE user_id = %s
        """,
        (g.user["user_id"],),
    )

    get_db().commit()
    return {"message": "All reminders and messages turned off."}


@reminders.post("/reminders/check")
@login_required()
def check_reminders():
    check_due_reminders()

    now = now_utc()
    ready = []

    for item in notification_list():
        if (
            item["status"] == "pending"
            or (
                item["status"] == "snoozed"
                and item["snoozed_until"] is not None
                and item["snoozed_until"] <= now
            )
        ):
            ready.append({
                "notification_id": item["notification_id"],
                "message": item["message"],
                "notification_method": item["notification_method"],
                "reminder_type": item["reminder_type"],
            })

    return {"notifications": ready}


def get_notification(notification_id):
    row = fetch_one(
        """
        SELECT notification_id
        FROM reminder_notifications
        WHERE notification_id = %s
          AND user_id = %s
          AND status IN ('pending', 'snoozed')
        """,
        (notification_id, g.user["user_id"]),
    )

    if row is None:
        raise ValueError("Notification not found")

    return row


@reminders.post("/reminders/notifications/<int:notification_id>/snooze")
@login_required()
def snooze_notification(notification_id):
    get_notification(notification_id)

    execute(
        """
        UPDATE reminder_notifications
        SET status = 'snoozed',
            snoozed_until = %s
        WHERE notification_id = %s AND user_id = %s
        """,
        (
            now_utc() + timedelta(minutes=10),
            notification_id,
            g.user["user_id"],
        ),
    )

    get_db().commit()
    return {"message": "Reminder snoozed for 10 minutes."}


@reminders.post("/reminders/notifications/<int:notification_id>/dismiss")
@login_required()
def dismiss_notification(notification_id):
    get_notification(notification_id)

    execute(
        """
        UPDATE reminder_notifications
        SET status = 'dismissed',
            snoozed_until = NULL
        WHERE notification_id = %s AND user_id = %s
        """,
        (notification_id, g.user["user_id"]),
    )

    get_db().commit()
    return {"message": "Reminder dismissed."}