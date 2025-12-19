from collections import defaultdict

from flask import Blueprint, render_template, request

from models import MenuItem

bp = Blueprint("menu", __name__)


@bp.get("/")
@bp.get("/menu")
def index():
    mode = (request.args.get("mode") or "online").lower()

    q = MenuItem.query

    if mode == "online":
        q = q.filter(MenuItem.is_available_online.is_(True))
    elif mode == "offline":
        q = q.filter(MenuItem.is_available_offline.is_(True))
    else:
        mode = "all"

    items = q.order_by(MenuItem.category.asc(), MenuItem.name.asc()).all()

    grouped = defaultdict(list)
    for item in items:
        grouped[item.category].append(item)

    return render_template("menu/index.html", grouped=grouped, mode=mode)
