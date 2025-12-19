from datetime import datetime
from io import BytesIO

from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from sqlalchemy import func
from xhtml2pdf import pisa

from auth_utils import login_required
from cart_utils import parse_items_spec
from extensions import db
from models import InventoryItem, MenuItem, Order, OrderItem

bp = Blueprint("staff", __name__, url_prefix="/staff")


@bp.get("/orders")
@login_required(role="staff")
def orders():
    pending = (
        Order.query.filter_by(mode="online")
        .filter(Order.status.in_(["pending"]))
        .order_by(Order.created_at.asc())
        .all()
    )
    return render_template("staff/orders.html", orders=pending)


@bp.post("/orders/<int:order_id>/confirm")
@login_required(role="staff")
def confirm_order(order_id: int):
    order = Order.query.get(order_id)
    if order is None:
        flash("Order not found.", "danger")
        return redirect(url_for("staff.orders"))

    order.status = "confirmed"
    db.session.commit()

    flash(f"Order #{order.id} confirmed.", "success")
    return redirect(url_for("staff.orders"))


@bp.post("/orders/<int:order_id>/cancel")
@login_required(role="staff")
def cancel_order(order_id: int):
    order = Order.query.get(order_id)
    if order is None:
        flash("Order not found.", "danger")
        return redirect(url_for("staff.orders"))

    order.status = "cancelled"
    db.session.commit()

    flash(f"Order #{order.id} cancelled.", "warning")
    return redirect(url_for("staff.orders"))


@bp.get("/counter")
@login_required(role="staff")
def counter_form():
    return render_template("staff/counter.html")


@bp.post("/orders/offline")
@login_required(role="staff")
def create_offline_order():
    spec = request.form.get("items_spec") or ""
    payment_mode = request.form.get("payment_mode") or "cash"
    discount_cents_str = (request.form.get("discount_cents") or "0").strip()
    customer_name = (request.form.get("customer_name") or "").strip() or "Walk-in"
    customer_phone = (request.form.get("customer_phone") or "").strip() or "-"

    try:
        discount_cents = int(discount_cents_str)
    except Exception:
        discount_cents = 0

    if discount_cents < 0:
        discount_cents = 0

    try:
        pairs = parse_items_spec(spec)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("staff.counter_form"))

    if not pairs:
        flash("No items provided.", "warning")
        return redirect(url_for("staff.counter_form"))

    ids = [item_id for item_id, _ in pairs]
    menu_items = MenuItem.query.filter(MenuItem.id.in_(ids)).all()
    by_id = {m.id: m for m in menu_items}

    cart_items: list[tuple[MenuItem, int]] = []
    for item_id, qty in pairs:
        mi = by_id.get(item_id)
        if mi is None:
            flash(f"Invalid item_id: {item_id}", "danger")
            return redirect(url_for("staff.counter_form"))
        if not mi.is_available_offline:
            flash(f"{mi.name} is not available for offline/POS ordering.", "warning")
            return redirect(url_for("staff.counter_form"))
        cart_items.append((mi, qty))

    subtotal_cents = sum(mi.price_cents * qty for mi, qty in cart_items)
    if discount_cents > subtotal_cents:
        discount_cents = subtotal_cents
    total_cents = subtotal_cents - discount_cents

    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        mode="offline",
        status="completed",
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        coupon_code=None,
        payment_mode=payment_mode,
        created_at=datetime.utcnow(),
    )

    for mi, qty in cart_items:
        unit = mi.price_cents
        line_total = unit * qty
        order.items.append(
            OrderItem(
                menu_item_id=mi.id,
                quantity=qty,
                unit_price_cents=unit,
                line_total_cents=line_total,
            )
        )

    db.session.add(order)
    db.session.flush()

    inv_rows = InventoryItem.query.filter(InventoryItem.menu_item_id.in_(ids)).all()
    inv_by_menu_id = {r.menu_item_id: r for r in inv_rows}

    for mi, qty in cart_items:
        inv = inv_by_menu_id.get(mi.id)
        if inv is not None:
            inv.stock = max(0, int(inv.stock) - int(qty))

    db.session.commit()

    flash(f"Offline order created: #{order.id}", "success")
    return redirect(url_for("orders.success", order_id=order.id))


@bp.get("/invoices/<int:order_id>.pdf")
@login_required(role="staff")
def invoice_pdf(order_id: int):
    order = Order.query.get(order_id)
    if order is None:
        flash("Order not found.", "danger")
        return redirect(url_for("staff.orders"))

    html = render_template("staff/invoice.html", order=order)

    pdf_io = BytesIO()
    result = pisa.CreatePDF(html, dest=pdf_io, encoding="utf-8")
    if result.err:
        flash("Failed to generate PDF.", "danger")
        return redirect(url_for("staff.orders"))

    response = make_response(pdf_io.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=invoice_{order.id}.pdf"
    return response
