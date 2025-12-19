from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from auth_utils import login_required
from extensions import db
from models import InventoryItem

bp = Blueprint("inventory", __name__, url_prefix="/staff")


@bp.get("/inventory")
@login_required(role="staff")
def inventory_list():
    rows = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return render_template("inventory/list.html", rows=rows)


@bp.post("/inventory/update")
@login_required(role="staff")
def inventory_update():
    item_id = request.form.get("item_id")
    stock = request.form.get("stock")

    try:
        item_id_int = int(item_id)
        stock_int = int(stock)
    except Exception:
        flash("Invalid input.", "danger")
        return redirect(url_for("inventory.inventory_list"))

    row = InventoryItem.query.get(item_id_int)
    if row is None:
        flash("Inventory item not found.", "danger")
        return redirect(url_for("inventory.inventory_list"))

    row.stock = max(0, stock_int)
    row.last_restock = datetime.utcnow()
    db.session.commit()

    flash("Stock updated.", "success")
    return redirect(url_for("inventory.inventory_list"))
