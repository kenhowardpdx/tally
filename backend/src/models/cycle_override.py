from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CycleOverride(Base):
    __tablename__ = "cycle_overrides"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "bill_id", "cycle_start_date", name="uq_cycle_overrides_bill_cycle"
        ),
        UniqueConstraint(
            "account_id",
            "windfall_id",
            "cycle_start_date",
            name="uq_cycle_overrides_windfall_cycle",
        ),
        CheckConstraint(
            "(bill_id IS NULL) != (windfall_id IS NULL)",
            name="ck_cycle_overrides_exactly_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True
    )
    bill_id: Mapped[int | None] = mapped_column(
        ForeignKey("bills.id", ondelete="CASCADE"), index=True
    )
    windfall_id: Mapped[int | None] = mapped_column(
        ForeignKey("windfalls.id", ondelete="CASCADE"), index=True
    )
    cycle_start_date: Mapped[date] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=true())
    override_amount_cents: Mapped[int | None] = mapped_column(BigInteger)
    notes: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bank_account: Mapped["BankAccount"] = relationship(back_populates="cycle_overrides")
    bill: Mapped["Bill | None"] = relationship(back_populates="cycle_overrides")
    windfall: Mapped["Windfall | None"] = relationship(back_populates="cycle_overrides")
