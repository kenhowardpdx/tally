import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, String, func, text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class RecurrenceType(str, enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    ANNUALLY = "annually"
    CUSTOM_DAYS = "custom_days"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    recurrence_type: Mapped[RecurrenceType] = mapped_column(
        Enum(
            RecurrenceType,
            name="recurrence_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    # Type-specific recurrence fields, e.g. {"day_of_month": 15} or
    # {"days": [10, 25]} for semimonthly, or {"interval_days": 45} for custom_days.
    # server_default (not just the ORM-side default) so raw SQL/admin-tool
    # inserts that bypass the ORM don't hit a NOT NULL violation.
    recurrence_config: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bank_account: Mapped["BankAccount"] = relationship(back_populates="bills")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="bill")
