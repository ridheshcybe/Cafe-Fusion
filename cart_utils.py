from flask import session


def get_cart() -> dict[str, int]:
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
    normalized = {}
    for k, v in cart.items():
        try:
            normalized[str(int(k))] = int(v)
        except Exception:
            continue
    session["cart"] = normalized
    return normalized


def set_cart(cart: dict[str, int]) -> None:
    session["cart"] = {str(int(k)): int(v) for k, v in cart.items()}


def clear_cart() -> None:
    session["cart"] = {}


def cart_count() -> int:
    cart = get_cart()
    return sum(int(qty) for qty in cart.values())


def parse_items_spec(spec: str) -> list[tuple[int, int]]:
    if not spec:
        return []

    parts = [p.strip() for p in spec.split(";") if p.strip()]
    items: list[tuple[int, int]] = []
    for p in parts:
        if ":" not in p:
            raise ValueError("Invalid format. Use item_id:qty;item_id:qty")
        item_id_s, qty_s = [x.strip() for x in p.split(":", 1)]
        item_id = int(item_id_s)
        qty = int(qty_s)
        if qty <= 0:
            raise ValueError("Quantity must be >= 1")
        items.append((item_id, qty))
    return items
