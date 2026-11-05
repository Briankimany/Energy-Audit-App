from server.extensions import db


class Building(db.Model):
    __tablename__ = "buildings"

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
    type = db.Column(db.String(100), nullable=False)
    floor_area_m2 = db.Column(db.Numeric(12, 2), nullable=False)
    operating_hours = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("institution_id", "name", name="uq_buildings_institution_name"),
        db.UniqueConstraint("institution_id", "id", name="uq_buildings_institution_id"),
        db.CheckConstraint("floor_area_m2 > 0", name="ck_buildings_floor_area_positive"),
        db.CheckConstraint(
            "operating_hours >= 1 AND operating_hours <= 24",
            name="ck_buildings_operating_hours_range",
        ),
    )
