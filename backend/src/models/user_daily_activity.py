from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class UserDailyActivity(Base):
    """Append-only record of which calendar days a user was active on.

    One row per (user_id, activity_date), written at most once per user per
    UTC day by `get_current_db_user`'s activity throttle. Durable history for
    MAU/DAU/WAU trend and cohort-retention queries, which a single mutable
    `users.last_active_at` timestamp can't reconstruct after time has passed.
    """

    __tablename__ = "user_daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_user_daily_activity_user_date"),
        Index("ix_user_daily_activity_activity_date", "activity_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    activity_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
