from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BankAccountCreate(BaseModel):
    name: str
    institution: str | None = None


class BankAccountUpdate(BaseModel):
    name: str | None = None
    institution: str | None = None


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    institution: str | None
    created_at: datetime
