from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from cart_utils import clear_cart, get_cart, parse_items_spec, set_cart
from extensions import db
from models import Coupon, MenuItem, Order, OrderItem
from email_utils import send_order_confirmation_email

bp = Blueprint("orders", __name__)


def _compute_totals(cart_items: list[tuple[MenuItem, int]], coupon_code: str | None):
    subtotal_cents = sum(item.price_cents * qty for item, qty in cart_items)

    discount_cents = 0
    applied_code = None

    if coupon_code:
        code = coupon_code.strip().upper()
        coupon = Coupon.query.filter_by(code=code, is_active=True).first()
        if coupon is None:
            raise ValueError("Invalid coupon code")
        if subtotal_cents < coupon.min_order_cents:
            raise ValueError("Order amount too low for this coupon")

        discount_cents = int(round(subtotal_cents * (coupon.discount_percent / 100.0)))
        if coupon.max_discount_cents and discount_cents > coupon.max_discount_cents:
            discount_cents = coupon.max_discount_cents
        if discount_cents > subtotal_cents:
            discount_cents = subtotal_cents
        applied_code = coupon.code

    total_cents = subtotal_cents - discount_cents
    return subtotal_cents, discount_cents, total_cents, applied_code


@bp.post("/cart/add")
def cart_add():
    item_id = request.form.get("item_id")
    qty = request.form.get("qty") or "1"

    try:
        item_id_int = int(item_id)
        qty_int = int(qty)
    except Exception:
        flash("Invalid item or quantity.", "danger")
        return redirect(url_for("menu.index"))

    if qty_int <= 0:
        flash("Quantity must be at least 1.", "warning")
        return redirect(url_for("menu.index"))

    item = MenuItem.query.get(item_id_int)
    if item is None:
        flash("Item not found.", "danger")
        return redirect(url_for("menu.index"))

    cart = get_cart()
    cart[str(item_id_int)] = int(cart.get(str(item_id_int), 0)) + qty_int
    set_cart(cart)

    flash(f"Added {qty_int} × {item.name} to cart.", "success")
    return redirect(request.referrer or url_for("menu.index"))


@bp.get("/cart")
def cart_view():
    cart = get_cart()
    ids = [int(k) for k in cart.keys()]
    items = MenuItem.query.filter(MenuItem.id.in_(ids)).all() if ids else []
    by_id = {i.id: i for i in items}

    cart_items: list[tuple[MenuItem, int]] = []
    for k, qty in cart.items():
        mi = by_id.get(int(k))
        if mi is None:
            continue
        cart_items.append((mi, int(qty)))

    subtotal_cents = sum(mi.price_cents * qty for mi, qty in cart_items)

    return render_template(
        "orders/cart.html",
        cart_items=cart_items,
        subtotal_cents=subtotal_cents,
    )


@bp.post("/cart/clear")
def cart_clear():
    clear_cart()
    flash("Cart cleared.", "info")
    return redirect(url_for("orders.cart_view"))


@bp.post("/cart/confirm")
def cart_confirm():
    cart = get_cart()
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("orders.cart_view"))

    customer_name = (request.form.get("customer_name") or "").strip()
    customer_phone = (request.form.get("customer_phone") or "").strip()
    customer_email = (request.form.get("customer_email") or "").strip()
    coupon_code = (request.form.get("coupon_code") or "").strip()

    if not all([customer_name, customer_phone, customer_email]):
        flash("Customer name, phone, and email are required.", "warning")
        return redirect(url_for("orders.cart_view"))

    ids = [int(k) for k in cart.keys()]
    menu_items = MenuItem.query.filter(MenuItem.id.in_(ids)).all()
    by_id = {m.id: m for m in menu_items}

    cart_items: list[tuple[MenuItem, int]] = []
    for k, qty in cart.items():
        mi = by_id.get(int(k))
        if mi is None:
            flash("One or more items in your cart no longer exist.", "danger")
            return redirect(url_for("orders.cart_view"))
        if not mi.is_available_online:
            flash(f"{mi.name} is not available for online ordering.", "warning")
            return redirect(url_for("orders.cart_view"))
        cart_items.append((mi, int(qty)))

    try:
        subtotal_cents, discount_cents, total_cents, applied_code = _compute_totals(
            cart_items, coupon_code or None
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.cart_view"))

    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        mode="online",
        status="pending",
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        coupon_code=applied_code,
        payment_mode=None,
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
    db.session.commit()

    try:
        send_order_confirmation_email(order)
    except Exception as e:
        current_app.logger.error(f"Failed to send order confirmation email: {e}")

    clear_cart()
    return redirect(url_for("orders.success", order_id=order.id))


@bp.get("/orders/success/<int:order_id>")
def success(order_id: int):
    order = Order.query.get(order_id)
    if order is None:
        flash("Order not found.", "danger")
        return redirect(url_for("menu.index"))
    return render_template("orders/success.html", order=order)


@bp.get("/orders/track")
def track_form():
    order_id = (request.args.get("order_id") or "").strip()
    if order_id:
        try:
            order_id_int = int(order_id)
            if order_id_int <= 0:
                raise ValueError()
        except Exception:
            flash("Please enter a valid order ID.", "warning")
            return render_template("orders/track.html")

        return redirect(url_for("orders.order_status", order_id=order_id_int))

    return render_template("orders/track.html")


@bp.get("/orders/<int:order_id>")
def order_status(order_id: int):
    order = Order.query.get(order_id)
    if order is None:
        return render_template("orders/not_found.html", order_id=order_id), 404

    label = {
        "pending": "🕒 Pending",
        "confirmed": "✅ Confirmed",
        "cancelled": "❌ Cancelled",
        "completed": "📦 Completed",
    }.get(order.status, order.status)

    return render_template("orders/status.html", order=order, label=label)


@bp.get("/order")
def manual_order_form():
    return render_template("orders/manual_order.html")


@bp.post("/manual/order")
def manual_order_post():
    data = request.form
    customer_name = (data.get("customer_name") or "").strip()
    customer_phone = (data.get("customer_phone") or "").strip()
    customer_email = (data.get("customer_email") or "").strip()
    mode = data.get("mode", "dine-in")
    payment_mode = data.get("payment_mode", "cash")
    status = data.get("status", "pending")

    if not customer_name or not customer_phone:
        flash("Customer name and phone are required.", "warning")
        return redirect(url_for("orders.manual_order_form"))

    try:
        pairs = parse_items_spec(data.get("items_spec") or "")
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.manual_order_form"))

    if not pairs:
        flash("No items provided.", "warning")
        return redirect(url_for("orders.manual_order_form"))

    ids = [item_id for item_id, _ in pairs]
    menu_items = MenuItem.query.filter(MenuItem.id.in_(ids)).all()
    by_id = {m.id: m for m in menu_items}

    cart_items: list[tuple[MenuItem, int]] = []
    for item_id, qty in pairs:
        mi = by_id.get(item_id)
        if mi is None:
            flash(f"Invalid item_id: {item_id}", "danger")
            return redirect(url_for("orders.manual_order_form"))
        if not mi.is_available_online:
            flash(f"{mi.name} is not available for online ordering.", "warning")
            return redirect(url_for("orders.manual_order_form"))
        cart_items.append((mi, qty))

    try:
        subtotal_cents, discount_cents, total_cents, applied_code = _compute_totals(
            cart_items, data.get("coupon_code") or None
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.manual_order_form"))

    order = Order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        mode=mode,
        status=status,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        coupon_code=applied_code,
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
    db.session.commit()

    if customer_email:
        try:
            send_order_confirmation_email(order)
        except Exception as e:
            current_app.logger.error(f"Failed to send order confirmation email: {e}")

    flash(f"Order #{order.id} created successfully.", "success")
    return redirect(url_for("orders.success", order_id=order.id))
