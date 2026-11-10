"""Shared validation for non-AI feature extensions."""

import math

from flask import g

from db import get_db


def user_id():
    return g.user["user_id"]


def commit():
    get_db().commit()


def clean_text(data, key, maximum, required=False):
    value = data.get(key, "")

    if not isinstance(value, str):
        raise ValueError(f"Invalid {key}")

    value = value.strip()

    if len(value) > maximum or (required and not value):
        raise ValueError(
            f"{key.replace('_', ' ').capitalize()} "
            f"must contain 1 to {maximum} characters"
            if required else f"{key} is too long"
        )

    return value


def whole_number(value, minimum=1, maximum=2147483647):
    if isinstance(value, bool):
        raise ValueError("Invalid whole number")

    try:
        result = int(str(value))
    except (TypeError, ValueError):
        raise ValueError("Enter a valid whole number")

    if not minimum <= result <= maximum:
        raise ValueError(
            f"Number must be between {minimum} and {maximum}"
        )

    return result


def optional_decimal(data, key, maximum):
    value = data.get(key)

    if value in ("", None):
        return None

    if isinstance(value, bool):
        raise ValueError(f"Invalid {key}")

    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {key}")

    if not math.isfinite(result) or not 0 <= result <= maximum:
        raise ValueError(f"Invalid {key}")

    return round(result, 3)