from server.extensions import db


class EnergyRecord(db.Model):
    __tablename__ = "energy_records"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    institution_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        nullable=False,
    )
    building_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        nullable=False,
    )
    month = db.Column(db.Date, nullable=False)
    kwh = db.Column(db.Numeric(14, 2), nullable=False)
    cost = db.Column(db.Numeric(14, 2), nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["institution_id", "building_id"],
            ["buildings.institution_id", "buildings.id"],
            ondelete="CASCADE",
            name="fk_energy_records_building",
        ),
        db.UniqueConstraint("building_id", "month", name="uq_energy_records_building_month"),
        db.CheckConstraint("kwh >= 0", name="ck_energy_records_kwh_non_negative"),
        db.CheckConstraint("cost >= 0", name="ck_energy_records_cost_non_negative"),
    )
