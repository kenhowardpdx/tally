from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.models.bill_event import BillEventType


class BillEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bill_id: int
    event_type: BillEventType
    cycle_start_date: date | None
    changes: dict | None
    created_at: datetime


class BillEventListResponse(BaseModel):
    bill_id: int
    total: int
    events: list[BillEventRead]
