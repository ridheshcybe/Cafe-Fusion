from datetime import datetime

from extensions import db
from models import Coupon, InventoryItem, MenuItem


def seed_data():
    db.create_all()

    sample_menu = [
        {
            "name": "Espresso",
            "category": "Coffee",
            "price_cents": 18000,
            "is_available_online": True,
            "is_available_offline": True,
        },
        {
            "name": "Cappuccino",
            "category": "Coffee",
            "price_cents": 24000,
            "is_available_online": True,
            "is_available_offline": True,
        },
        {
            "name": "Cold Brew",
            "category": "Coffee",
            "price_cents": 26000,
            "is_available_online": True,
            "is_available_offline": True,
        },
        {
            "name": "Masala Chai",
            "category": "Tea",
            "price_cents": 12000,
            "is_available_online": True,
            "is_available_offline": True,
        },
        {
            "name": "Veg Sandwich",
            "category": "Snacks",
            "price_cents": 22000,
            "is_available_online": True,
            "is_available_offline": True,
        },
        {
            "name": "Chocolate Muffin",
            "category": "Snacks",
            "price_cents": 15000,
            "is_available_online": True,
            "is_available_offline": True,
        },
    ]

    existing_names = {m.name for m in MenuItem.query.all()}
    for row in sample_menu:
        if row["name"] in existing_names:
            continue
        db.session.add(MenuItem(**row))

    db.session.commit()

    for mi in MenuItem.query.all():
        inv = InventoryItem.query.filter_by(menu_item_id=mi.id).first()
        if inv is None:
            db.session.add(
                InventoryItem(
                    menu_item_id=mi.id,
                    name=mi.name,
                    stock=25,
                    last_restock=datetime.utcnow(),
                )
            )

    coupons = [
        {
            "code": "FUSION10",
            "discount_percent": 10,
            "min_order_cents": 30000,
            "max_discount_cents": 5000,
            "is_active": True,
        },
        {
            "code": "WELCOME15",
            "discount_percent": 15,
            "min_order_cents": 50000,
            "max_discount_cents": 10000,
            "is_active": True,
        },
    ]

    existing_codes = {c.code for c in Coupon.query.all()}
    for c in coupons:
        if c["code"] in existing_codes:
            continue
        db.session.add(Coupon(**c))

    db.session.commit()
    print("Seed complete: menu items, inventory, coupons")
