from flask import Blueprint, render_template
from sqlalchemy import func

from auth_utils import login_required
from extensions import db
from models import Order

bp = Blueprint("reports", __name__, url_prefix="/staff")


@bp.get("/reports")
@login_required(role="staff")
def reports_index():
    per_day = (
        db.session.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total_cents), 0).label("revenue_cents"),
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at).desc())
        .limit(14)
        .all()
    )

    mode_counts = (
        db.session.query(Order.mode, func.count(Order.id))
        .group_by(Order.mode)
        .all()
    )

    status_counts = (
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )

    return render_template(
        "reports/index.html",
        per_day=per_day,
        mode_counts=mode_counts,
        status_counts=status_counts,
    )
