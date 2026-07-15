from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WindfallCreate(BaseModel):
    name: str
    # Always positive - a windfall is income by definition.
    amount_cents: int = Field(gt=0)
    expected_date: date
    enabled: bool = True


class WindfallUpdate(BaseModel):
    name: str | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    expected_date: date | None = None
    enabled: bool | None = None
    account_id: int | None = None


class WindfallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    name: str
    amount_cents: int
    expected_date: date
    enabled: bool
    created_at: datetime


class WindfallImportRowIssue(BaseModel):
    row: int
    message: str


class WindfallImportAmbiguous(BaseModel):
    # No row number - describes a match collision found during
    # reconciliation, not a single malformed CSV row.
    message: str


class WindfallImportUpdate(BaseModel):
    id: int
    fields: WindfallCreate


class WindfallImportPreview(BaseModel):
    new: list[WindfallCreate]
    updated: list[WindfallImportUpdate]
    unchanged_count: int
    ambiguous: list[WindfallImportAmbiguous]
    # Currently-enabled windfalls that will be disabled (not deleted - see
    # cycle_overrides) if this preview is committed.
    omitted: list[WindfallRead]
    errors: list[WindfallImportRowIssue]


class WindfallImportCommitRequest(BaseModel):
    new: list[WindfallCreate]
    updated: list[WindfallImportUpdate]
    omitted_ids: list[int]


class WindfallImportCommitResponse(BaseModel):
    created: list[WindfallRead]
    updated: list[WindfallRead]
    disabled_count: int
