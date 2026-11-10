"""UC08: Friends, posts, likes and comments."""

from flask import Blueprint, g, render_template, request

from accounts import login_required
from db import execute, fetch_all, fetch_one, get_db
from validation import payload, text

social = Blueprint("social", __name__)


def uid():
    return g.user["user_id"]


def friend_condition(alias="f"):
    return f"""
        EXISTS (
            SELECT 1 FROM friendships {alias}
            WHERE {alias}.status = 'accepted'
              AND (
                ({alias}.requester_id = %s
                 AND {alias}.addressee_id = p.user_id)
                OR
                ({alias}.addressee_id = %s
                 AND {alias}.requester_id = p.user_id)
              )
        )
    """


def can_view_post(post_id):
    return fetch_one(
        """
        SELECT p.post_id, p.user_id
        FROM social_posts p
        WHERE p.post_id = %s
          AND (
            p.user_id = %s
            OR
        """ + friend_condition() + """
          )
        """,
        (post_id, uid(), uid(), uid()),
    )


def read_friends():
    return fetch_all(
        """
        SELECT u.user_id, u.first_name, u.last_name
        FROM friendships f
        JOIN users u ON u.user_id =
            CASE WHEN f.requester_id = %s
                 THEN f.addressee_id
                 ELSE f.requester_id END
        WHERE f.status = 'accepted'
          AND (f.requester_id = %s OR f.addressee_id = %s)
          AND u.status = 'active'
        ORDER BY u.first_name, u.last_name
        """,
        (uid(), uid(), uid()),
    )


def read_feed():
    return fetch_all(
        """
        SELECT p.post_id, p.user_id, p.content, p.created_at,
               u.first_name, u.last_name,
               (SELECT COUNT(*) FROM social_likes l
                WHERE l.post_id = p.post_id) AS like_count,
               (SELECT COUNT(*) FROM social_likes l
                WHERE l.post_id = p.post_id AND l.user_id = %s)
                AS liked_by_me
        FROM social_posts p
        JOIN users u ON u.user_id = p.user_id
        WHERE u.status = 'active'
          AND (
            p.user_id = %s
            OR
        """ + friend_condition() + """
          )
        ORDER BY p.created_at DESC, p.post_id DESC
        LIMIT 50
        """,
        (uid(), uid(), uid(), uid()),
    )


def read_comments(post_ids):
    if not post_ids:
        return []

    placeholders = ", ".join(["%s"] * len(post_ids))

    return fetch_all(
        f"""
        SELECT c.comment_id, c.post_id, c.user_id,
               c.content, c.created_at,
               u.first_name, u.last_name
        FROM social_comments c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.post_id IN ({placeholders})
          AND u.status = 'active'
        ORDER BY c.created_at, c.comment_id
        """,
        tuple(post_ids),
    )


@social.get("/social")
@login_required(html=True)
def social_page():
    search = request.args.get("q", "").strip()[:80]

    people = []
    if search:
        people = fetch_all(
            """
            SELECT user_id, first_name, last_name
            FROM users
            WHERE user_id <> %s
              AND status = 'active'
              AND (
                first_name LIKE %s
                OR last_name LIKE %s
              )
            ORDER BY first_name, last_name
            LIMIT 30
            """,
            (uid(), f"%{search}%", f"%{search}%"),
        )

    incoming = fetch_all(
        """
        SELECT f.friendship_id, u.first_name, u.last_name
        FROM friendships f
        JOIN users u ON u.user_id = f.requester_id
        WHERE f.addressee_id = %s
          AND f.status = 'pending'
          AND u.status = 'active'
        ORDER BY f.created_at DESC
        """,
        (uid(),),
    )

    outgoing = fetch_all(
        """
        SELECT f.friendship_id, u.first_name, u.last_name
        FROM friendships f
        JOIN users u ON u.user_id = f.addressee_id
        WHERE f.requester_id = %s
          AND f.status = 'pending'
        ORDER BY f.created_at DESC
        """,
        (uid(),),
    )

    friendships = fetch_all(
        """
        SELECT friendship_id, requester_id, addressee_id, status
        FROM friendships
        WHERE requester_id = %s OR addressee_id = %s
        """,
        (uid(), uid()),
    )

    feed = read_feed()
    comments = read_comments([p["post_id"] for p in feed])

    comments_by_post = {}
    for comment in comments:
        comments_by_post.setdefault(comment["post_id"], []).append(comment)

    return render_template(
        "social.html",
        people=people,
        search=search,
        incoming=incoming,
        outgoing=outgoing,
        friendships=friendships,
        friends=read_friends(),
        feed=feed,
        comments_by_post=comments_by_post,
        current_user_id=uid(),
    )


@social.post("/social/friends/<int:user_id>")
@login_required()
def send_friend_request(user_id):
    if user_id == uid():
        raise ValueError("You cannot add yourself")

    other = fetch_one(
        "SELECT user_id FROM users WHERE user_id = %s AND status = 'active'",
        (user_id,),
    )
    if not other:
        return {"error": "User not found"}, 404

    existing = fetch_one(
        """
        SELECT friendship_id FROM friendships
        WHERE (requester_id = %s AND addressee_id = %s)
           OR (requester_id = %s AND addressee_id = %s)
        """,
        (uid(), user_id, user_id, uid()),
    )
    if existing:
        return {"error": "A friendship or request already exists"}, 409

    execute(
        """
        INSERT INTO friendships (requester_id, addressee_id)
        VALUES (%s, %s)
        """,
        (uid(), user_id),
    )
    get_db().commit()
    return {"message": "Friend request sent."}, 201


@social.post("/social/friends/<int:friendship_id>/accept")
@login_required()
def accept_friend_request(friendship_id):
    _, changed = execute(
        """
        UPDATE friendships
        SET status = 'accepted'
        WHERE friendship_id = %s
          AND addressee_id = %s
          AND status = 'pending'
        """,
        (friendship_id, uid()),
    )
    if not changed:
        return {"error": "Request not found"}, 404

    get_db().commit()
    return {"message": "Friend request accepted."}


@social.delete("/social/friends/<int:friendship_id>")
@login_required()
def remove_friendship(friendship_id):
    _, changed = execute(
        """
        DELETE FROM friendships
        WHERE friendship_id = %s
          AND (requester_id = %s OR addressee_id = %s)
        """,
        (friendship_id, uid(), uid()),
    )
    if not changed:
        return {"error": "Friendship or request not found"}, 404

    get_db().commit()
    return {"message": "Friendship or request removed."}


@social.post("/social/posts")
@login_required()
def create_post():
    content = text(payload(), "content", 1000)

    execute(
        "INSERT INTO social_posts (user_id, content) VALUES (%s, %s)",
        (uid(), content),
    )
    get_db().commit()
    return {"message": "Update shared with your friends."}, 201


@social.delete("/social/posts/<int:post_id>")
@login_required()
def delete_post(post_id):
    _, changed = execute(
        "DELETE FROM social_posts WHERE post_id = %s AND user_id = %s",
        (post_id, uid()),
    )
    if not changed:
        return {"error": "Post not found"}, 404

    get_db().commit()
    return {"message": "Post deleted."}


@social.post("/social/posts/<int:post_id>/like")
@login_required()
def toggle_like(post_id):
    if not can_view_post(post_id):
        return {"error": "Post not found"}, 404

    existing = fetch_one(
        "SELECT post_id FROM social_likes WHERE post_id = %s AND user_id = %s",
        (post_id, uid()),
    )

    if existing:
        execute(
            "DELETE FROM social_likes WHERE post_id = %s AND user_id = %s",
            (post_id, uid()),
        )
        message = "Like removed."
    else:
        execute(
            "INSERT INTO social_likes (post_id, user_id) VALUES (%s, %s)",
            (post_id, uid()),
        )
        message = "Post liked."

    get_db().commit()
    return {"message": message}


@social.post("/social/posts/<int:post_id>/comments")
@login_required()
def add_comment(post_id):
    if not can_view_post(post_id):
        return {"error": "Post not found"}, 404

    content = text(payload(), "content", 500)

    execute(
        """
        INSERT INTO social_comments (post_id, user_id, content)
        VALUES (%s, %s, %s)
        """,
        (post_id, uid(), content),
    )
    get_db().commit()
    return {"message": "Comment added."}, 201


@social.delete("/social/comments/<int:comment_id>")
@login_required()
def delete_comment(comment_id):
    _, changed = execute(
        """
        DELETE FROM social_comments
        WHERE comment_id = %s AND user_id = %s
        """,
        (comment_id, uid()),
    )
    if not changed:
        return {"error": "Comment not found"}, 404

    get_db().commit()
    return {"message": "Comment deleted."}