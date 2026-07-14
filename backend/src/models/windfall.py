from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.bank_account import BankAccount
    from src.models.cycle_override import CycleOverride


class Windfall(Base):
    __tablename__ = "windfalls"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True
    )
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    expected_date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    bank_account: Mapped["BankAccount"] = relationship(back_populates="windfalls")
    cycle_overrides: Mapped[list["CycleOverride"]] = relationship(
        back_populates="windfall", cascade="all, delete-orphan"
    )
