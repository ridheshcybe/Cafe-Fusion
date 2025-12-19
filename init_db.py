from extensions import db
from models import Coupon, InventoryItem, MenuItem, Order, OrderItem, User
from app import create_app

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created (if they didn't exist).")

if __name__ == "__main__":
    init_db()
