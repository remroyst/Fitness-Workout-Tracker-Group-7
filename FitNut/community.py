"""Community features: messaging, safety and challenges."""

from datetime import date

from flask import Blueprint, g, render_template

from accounts import login_required
from db import execute, fetch_all, fetch_one
from feature_utils import (
    user_id,
    commit,
    clean_text,
    whole_number,
)
from validation import payload

community = Blueprint("community", __name__)


def user_exists(other):
    return fetch_one(
        """
        SELECT user_id
        FROM users
        WHERE user_id = %s AND status = 'active'
        """,
        (other,),
    ) is not None


def is_blocked(other):
    return fetch_one(
        """
        SELECT 1 FROM social_blocks
        WHERE
            (blocker_id = %s AND blocked_id = %s)
            OR
            (blocker_id = %s AND blocked_id = %s)
        """,
        (user_id(), other, other, user_id()),
    ) is not None


def is_friend(other):
    return fetch_one(
        """
        SELECT 1
        FROM friendships
        WHERE status = 'accepted'
          AND (
            (requester_id = %s AND addressee_id = %s)
            OR
            (requester_id = %s AND addressee_id = %s)
          )
        """,
        (user_id(), other, other, user_id()),
    ) is not None


@community.get("/community")
@login_required(html=True)
def community_page():
    friends = fetch_all(
        """
        SELECT u.user_id, u.first_name, u.last_name
        FROM friendships f
        JOIN users u ON u.user_id =
            CASE
              WHEN f.requester_id = %s THEN f.addressee_id
              ELSE f.requester_id
            END
        WHERE f.status = 'accepted'
          AND (f.requester_id = %s OR f.addressee_id = %s)
          AND u.status = 'active'
          AND NOT EXISTS (
            SELECT 1 FROM social_blocks b
            WHERE
              (b.blocker_id = %s AND b.blocked_id = u.user_id)
              OR
              (b.blocker_id = u.user_id AND b.blocked_id = %s)
          )
        ORDER BY u.first_name, u.last_name
        """,
        (
            user_id(), user_id(), user_id(),
            user_id(), user_id(),
        ),
    )

    messages = fetch_all(
        """
        SELECT m.message_id, m.sender_id,
               m.recipient_id, m.content, m.created_at,
               u.first_name, u.last_name
        FROM social_messages m
        JOIN users u ON u.user_id = m.sender_id
        WHERE (m.sender_id = %s OR m.recipient_id = %s)
          AND NOT EXISTS (
            SELECT 1 FROM social_blocks b
            WHERE
              (b.blocker_id = m.sender_id
               AND b.blocked_id = m.recipient_id)
              OR
              (b.blocker_id = m.recipient_id
               AND b.blocked_id = m.sender_id)
          )
        ORDER BY m.created_at DESC, m.message_id DESC
        LIMIT 50
        """,
        (user_id(), user_id()),
    )

    challenges = fetch_all(
        """
        SELECT c.challenge_id, c.title, c.description,
               c.target_minutes, c.start_date, c.end_date,
               EXISTS (
                 SELECT 1 FROM challenge_participants p
                 WHERE p.challenge_id = c.challenge_id
                   AND p.user_id = %s
               ) AS joined,
               (
                 SELECT COUNT(*)
                 FROM challenge_participants p
                 WHERE p.challenge_id = c.challenge_id
               ) AS participant_count
        FROM fitness_challenges c
        WHERE c.end_date >= CURRENT_DATE()
        ORDER BY c.start_date DESC
        LIMIT 40
        """,
        (user_id(),),
    )

    blocked_users = fetch_all(
        """
        SELECT u.user_id, u.first_name, u.last_name
        FROM social_blocks b
        JOIN users u ON u.user_id = b.blocked_id
        WHERE b.blocker_id = %s
        ORDER BY u.first_name
        """,
        (user_id(),),
    )

    return render_template(
        "community.html",
        friends=friends,
        messages=messages,
        challenges=challenges,
        blocked_users=blocked_users,
        current_user_id=user_id(),
    )


@community.post("/api/community/messages")
@login_required()
def send_message():
    data = payload()

    recipient = whole_number(data.get("recipient_id"))
    content = clean_text(data, "content", 2000, required=True)

    if recipient == user_id():
        raise ValueError("You cannot message yourself")

    if not user_exists(recipient):
        return {"error": "User not found"}, 404

    if is_blocked(recipient) or not is_friend(recipient):
        return {
            "error": "You can only message unblocked friends"
        }, 403

    execute(
        """
        INSERT INTO social_messages
            (sender_id, recipient_id, content)
        VALUES (%s, %s, %s)
        """,
        (user_id(), recipient, content),
    )

    commit()
    return {"message": "Message sent"}, 201


@community.post("/api/community/block")
@login_required()
def block_user():
    data = payload()
    other = whole_number(data.get("user_id"))

    if other == user_id():
        raise ValueError("You cannot block yourself")

    if not user_exists(other):
        return {"error": "User not found"}, 404

    execute(
        """
        INSERT IGNORE INTO social_blocks
            (blocker_id, blocked_id)
        VALUES (%s, %s)
        """,
        (user_id(), other),
    )

    execute(
        """
        DELETE FROM friendships
        WHERE
            (requester_id = %s AND addressee_id = %s)
            OR
            (requester_id = %s AND addressee_id = %s)
        """,
        (user_id(), other, other, user_id()),
    )

    commit()
    return {"message": "User blocked"}


@community.post("/api/community/unblock")
@login_required()
def unblock_user():
    other = whole_number(payload().get("user_id"))

    execute(
        """
        DELETE FROM social_blocks
        WHERE blocker_id = %s AND blocked_id = %s
        """,
        (user_id(), other),
    )

    commit()
    return {"message": "User unblocked"}


@community.post("/api/community/report")
@login_required()
def report_user():
    data = payload()

    other = whole_number(data.get("user_id"))
    reason = clean_text(data, "reason", 500, required=True)

    if other == user_id():
        raise ValueError("You cannot report yourself")

    if not user_exists(other):
        return {"error": "User not found"}, 404

    post_id = data.get("post_id") or None

    if post_id is not None:
        post_id = whole_number(post_id)

        post = fetch_one(
            """
            SELECT post_id
            FROM social_posts
            WHERE post_id = %s AND user_id = %s
            """,
            (post_id, other),
        )

        if not post:
            return {"error": "Post not found"}, 404

    execute(
        """
        INSERT INTO social_reports
            (reporter_id, reported_user_id, post_id, reason)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id(), other, post_id, reason),
    )

    commit()
    return {"message": "Report submitted"}, 201


@community.post("/api/community/challenges")
@login_required()
def create_challenge():
    data = payload()

    title = clean_text(data, "title", 120, required=True)
    description = clean_text(data, "description", 500)
    target = whole_number(
        data.get("target_minutes"), 1, 100000
    )

    try:
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Enter valid challenge dates")

    if end < start or end < date.today():
        raise ValueError("Challenge end date must be in the future")

    challenge_id, _ = execute(
        """
        INSERT INTO fitness_challenges (
            creator_id, title, description,
            target_minutes, start_date, end_date
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id(), title, description,
            target, start, end,
        ),
    )

    execute(
        """
        INSERT INTO challenge_participants
            (challenge_id, user_id)
        VALUES (%s, %s)
        """,
        (challenge_id, user_id()),
    )

    commit()
    return {"message": "Challenge created"}, 201


@community.post("/api/community/challenges/<int:challenge_id>/join")
@login_required()
def join_challenge(challenge_id):
    challenge = fetch_one(
        """
        SELECT challenge_id
        FROM fitness_challenges
        WHERE challenge_id = %s
          AND end_date >= CURRENT_DATE()
        """,
        (challenge_id,),
    )

    if not challenge:
        return {"error": "Challenge unavailable"}, 404

    execute(
        """
        INSERT IGNORE INTO challenge_participants
            (challenge_id, user_id)
        VALUES (%s, %s)
        """,
        (challenge_id, user_id()),
    )

    commit()
    return {"message": "Challenge joined"}


@community.get(
    "/api/community/challenges/<int:challenge_id>/progress"
)
@login_required()
def challenge_progress(challenge_id):
    challenge = fetch_one(
        """
        SELECT target_minutes, start_date, end_date
        FROM fitness_challenges
        WHERE challenge_id = %s
        """,
        (challenge_id,),
    )

    if not challenge:
        return {"error": "Challenge not found"}, 404

    participant = fetch_one(
        """
        SELECT 1
        FROM challenge_participants
        WHERE challenge_id = %s AND user_id = %s
        """,
        (challenge_id, user_id()),
    )

    if not participant:
        return {"error": "Join the challenge first"}, 403

    result = fetch_one(
        """
        SELECT COALESCE(
            SUM(
                TIMESTAMPDIFF(
                    SECOND, time_started, time_finished
                )
            ), 0
        ) AS seconds
        FROM activity_events
        WHERE user_id = %s
          AND DATE(time_started) BETWEEN %s AND %s
        """,
        (
            user_id(),
            challenge["start_date"],
            challenge["end_date"],
        ),
    )

    minutes = round(result["seconds"] / 60, 1)

    return {
        "minutes": minutes,
        "target_minutes": challenge["target_minutes"],
        "completed": minutes >= challenge["target_minutes"],
    }