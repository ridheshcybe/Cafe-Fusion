from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from extensions import db
from models import User

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user.id
    session["email"] = user.email
    session["role"] = user.role

    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)

    if user.role == "staff":
        return redirect(url_for("staff.orders"))

    return redirect(url_for("menu.index"))


@bp.get("/register")
def register():
    return render_template("auth/register.html")


@bp.post("/register")
def register_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "warning")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first() is not None:
        flash("That email is already registered.", "warning")
        return redirect(url_for("auth.register"))

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role="customer",
    )
    db.session.add(user)
    db.session.commit()

    flash("Account created. Please log in.", "success")
    return redirect(url_for("auth.login"))


@bp.get("/staff/register")
def staff_register():
    return render_template("auth/staff_register.html")


@bp.post("/staff/register")
def staff_register_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    setup_code = request.form.get("setup_code") or ""

    if setup_code != Config.STAFF_SETUP_CODE:
        flash("Invalid staff setup code.", "danger")
        return redirect(url_for("auth.staff_register"))

    if not email or not password:
        flash("Email and password are required.", "warning")
        return redirect(url_for("auth.staff_register"))

    if User.query.filter_by(email=email).first() is not None:
        flash("That email is already registered.", "warning")
        return redirect(url_for("auth.staff_register"))

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role="staff",
    )
    db.session.add(user)
    db.session.commit()

    flash("Staff account created. Please log in.", "success")
    return redirect(url_for("auth.login"))


@bp.post("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("menu.index"))
