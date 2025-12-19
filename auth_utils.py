from functools import wraps

from flask import flash, redirect, request, session, url_for

from models import User


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.path))

            if role is not None:
                user_role = session.get("role")
                if user_role != role:
                    flash("You are not allowed to access that page.", "danger")
                    return redirect(url_for("menu.index"))

            return fn(*args, **kwargs)

        return wrapper

    return decorator
