from datetime import datetime, timezone

from server.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    institution_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="auditor")
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
