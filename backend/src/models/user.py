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

    bank_accounts: Mapped[list["BankAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
