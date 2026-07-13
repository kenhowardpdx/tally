from datetime import datetime

from pydantic import BaseModel


class ConsentStatus(BaseModel):
    terms_accepted: bool
    terms_accepted_at: datetime | None
