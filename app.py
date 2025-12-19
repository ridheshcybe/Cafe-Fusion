from datetime import datetime

from flask import Flask

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from models import Coupon, InventoryItem, MenuItem, Order, OrderItem, User

        @app.template_filter("money")
        def money(cents: int) -> str:
            if cents is None:
                return "₹0.00"
            return f"₹{cents / 100:.2f}"

        @app.context_processor
        def inject_globals():
            from auth_utils import current_user
            from cart_utils import cart_count

            return {
                "current_user": current_user,
                "cart_count": cart_count,
                "now": datetime.utcnow,
            }

        @app.cli.command("seed")
        def seed_command():
            from seed import seed_data

            seed_data()

    from blueprints.admin import bp as admin_bp
    from blueprints.auth import bp as auth_bp
    from blueprints.inventory import bp as inventory_bp
    from blueprints.menu import bp as menu_bp
    from blueprints.orders import bp as orders_bp
    from blueprints.reports import bp as reports_bp
    from blueprints.staff import bp as staff_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
