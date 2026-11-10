"""UC01: User profile management."""

import re

import mysql.connector
from flask import Blueprint, g, render_template
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from accounts import login_required
from db import execute, fetch_one, get_db
from validation import payload, text

profile = Blueprint("profile", __name__)


@profile.get("/profile")
@login_required(html=True)
def profile_page():
    return render_template("profile.html", user=g.user)


@profile.post("/profile")
@login_required()
def update_profile():
    data = payload()

    first_name = text(data, "first_name", 50)
    last_name = text(data, "last_name", 50)
    email = text(data, "email", 254).lower()

    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Enter a valid email address")

    try:
        execute(
            """
            UPDATE users
            SET first_name = %s,
                last_name = %s,
                email = %s
            WHERE user_id = %s
            """,
            (
                first_name,
                last_name,
                email,
                g.user["user_id"],
            ),
        )
        get_db().commit()

    except mysql.connector.IntegrityError as error:
        get_db().rollback()

        if error.errno == 1062:
            return {"error": "Email address is already in use"}, 409

        raise

    return {"message": "Profile updated successfully."}


@profile.post("/profile/password")
@login_required()
def change_password():
    data = payload()

    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirmation = data.get("password_confirmation")

    if not isinstance(current_password, str):
        raise ValueError("Enter your current password")

    if (
        not isinstance(new_password, str)
        or not 8 <= len(new_password) <= 128
        or not new_password.strip()
    ):
        raise ValueError(
            "New password must contain 8 to 128 characters"
        )

    if new_password != confirmation:
        raise ValueError("New passwords do not match")

    user = fetch_one(
        """
        SELECT password_hash
        FROM users
        WHERE user_id = %s
        """,
        (g.user["user_id"],),
    )

    if not user or not check_password_hash(
        user["password_hash"], current_password
    ):
        return {"error": "Current password is incorrect"}, 400

    if check_password_hash(user["password_hash"], new_password):
        raise ValueError(
            "New password must be different from your current password"
        )

    execute(
        """
        UPDATE users
        SET password_hash = %s
        WHERE user_id = %s
        """,
        (
            generate_password_hash(new_password),
            g.user["user_id"],
        ),
    )

    # Revoke other sessions after a password change.
    execute(
        """
        UPDATE sessions
        SET revoked_at = UTC_TIMESTAMP(6)
        WHERE user_id = %s
          AND token_hash <> %s
          AND revoked_at IS NULL
        """,
        (
            g.user["user_id"],
            __import__("hashlib").sha256(
                g.session_token.encode()
            ).hexdigest(),
        ),
    )

    get_db().commit()

    return {
        "message": "Password changed successfully. "
                   "Other sessions have been signed out."
    }