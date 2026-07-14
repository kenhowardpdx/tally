import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.bill import Bill
    from src.models.cycle_override import CycleOverride
    from src.models.transaction import Transaction
    from src.models.user import User
    from src.models.windfall import Windfall


class CycleType(enum.StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    SEMIMONTHLY = "semimonthly"


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    institution: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Last-used forecast settings, persisted so revisiting the forecast page
    # doesn't require re-entering the starting balance/date range every time -
    # pay cycles are ~2 weeks apart and users check back on the same cycle
    # repeatedly. Set as a side effect of POST .../forecast, not editable
    # directly (no equivalent field on BankAccountUpdate).
    forecast_starting_balance_cents: Mapped[int | None] = mapped_column(BigInteger)
    forecast_income_per_cycle_cents: Mapped[int | None] = mapped_column(BigInteger)
    forecast_cycle_type: Mapped[CycleType | None] = mapped_column(
        Enum(
            CycleType,
            name="cycle_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    forecast_start_date: Mapped[date | None] = mapped_column(Date)
    forecast_end_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="bank_accounts")
    bills: Mapped[list["Bill"]] = relationship(
        back_populates="bank_account", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="bank_account", cascade="all, delete-orphan"
    )
    windfalls: Mapped[list["Windfall"]] = relationship(
        back_populates="bank_account", cascade="all, delete-orphan"
    )
    cycle_overrides: Mapped[list["CycleOverride"]] = relationship(
        back_populates="bank_account", cascade="all, delete-orphan"
    )
