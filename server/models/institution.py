from datetime import datetime, timezone
from decimal import Decimal

from server.extensions import db


class Institution(db.Model):
    __tablename__ = "institutions"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    name = db.Column(db.String(255), nullable=False, unique=True)
    currency = db.Column(db.String(3), nullable=False, default="KES")
    standard_cost_per_kwh = db.Column(
        db.Numeric(10, 4),
        nullable=False,
        default=Decimal("21.84"),
        server_default="21.84",
    )
    max_buildings = db.Column(db.Integer, nullable=False, default=5)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    users = db.relationship("User", backref="institution", lazy=True)
