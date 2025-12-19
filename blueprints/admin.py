from flask import Blueprint, flash, redirect, render_template, request, url_for

from auth_utils import login_required
from extensions import db
from models import MenuItem

bp = Blueprint("admin", __name__, url_prefix="/staff")


@bp.get("/menu/add")
@login_required(role="staff")
def menu_add_form():
    return render_template("admin/menu_add.html")


@bp.post("/menu/add")
@login_required(role="staff")
def menu_add_post():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price_cents = request.form.get("price_cents")
    online = bool(request.form.get("is_available_online"))
    offline = bool(request.form.get("is_available_offline"))

    if not name or not category or not price_cents:
        flash("All fields are required.", "warning")
        return redirect(url_for("admin.menu_add_form"))

    try:
        price_cents_int = int(price_cents)
    except Exception:
        flash("Invalid price.", "danger")
        return redirect(url_for("admin.menu_add_form"))

    mi = MenuItem(
        name=name,
        category=category,
        price_cents=price_cents_int,
        is_available_online=online,
        is_available_offline=offline,
    )
    db.session.add(mi)
    db.session.commit()

    flash(f"Added {name}.", "success")
    return redirect(url_for("menu.index"))
