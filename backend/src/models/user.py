from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    auth0_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Nullable: Auth0 access tokens for a custom API audience don't carry
    # profile claims like email by default (that needs a custom Auth0
    # Action), so it's not reliably available at JIT-provisioning time.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Null until the user accepts the Privacy Policy/Terms via the frontend's
    # consent interstitial ((app)/+layout.svelte) - tracked here rather than
    # in Auth0 because the tenant/Universal Login page isn't managed by this
    # codebase (it's a manual console step - see docs/ROADMAP.md's Phase 0
    # notes), so there's no infra-as-code hook to add a signup-time checkbox
    # there consistently across environments. See docs/ROADMAP.md's
    # consent-tracking note for the full tradeoff.
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Updated at most once/hour by get_current_db_user (backend/src/api/deps.py) - a
    # cheap write-throttle guard, not a source of historical trends. Durable
    # per-day history for MAU/DAU/retention queries lives in `user_daily_activity`.
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    bank_accounts: Mapped[list["BankAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
