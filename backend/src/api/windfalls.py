from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_bank_account_or_404, get_current_db_user, get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, User, Windfall
from src.schemas.windfall import (
    WindfallCreate,
    WindfallImportAmbiguous,
    WindfallImportCommitRequest,
    WindfallImportCommitResponse,
    WindfallImportPreview,
    WindfallImportUpdate,
    WindfallRead,
    WindfallUpdate,
)
from src.windfalls_csv import parse_csv_rows, reconcile_windfalls, windfalls_to_csv

router = APIRouter(prefix="/api/v1/accounts/{account_id}/windfalls", tags=["windfalls"])

_NON_NULLABLE_UPDATE_FIELDS = ("name", "amount_cents", "expected_date", "enabled")


def _reject_explicit_nulls(update_data: dict) -> None:
    nulled = [
        field
        for field in _NON_NULLABLE_UPDATE_FIELDS
        if field in update_data and update_data[field] is None
    ]
    if nulled:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field(s) cannot be null: {', '.join(nulled)}",
        )


async def _get_owned_windfall(
    windfall_id: int,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Windfall:
    result = await db.execute(
        select(Windfall).where(Windfall.id == windfall_id, Windfall.account_id == account.id)
    )
    windfall = result.scalar_one_or_none()
    if windfall is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Windfall not found")
    return windfall


@router.get("", response_model=list[WindfallRead])
async def list_windfalls(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[Windfall]:
    result = await db.execute(
        select(Windfall)
        .where(Windfall.account_id == account.id)
        .order_by(Windfall.expected_date.asc(), Windfall.id.asc())
    )
    return list(result.scalars().all())


@router.post("", response_model=WindfallRead, status_code=status.HTTP_201_CREATED)
async def create_windfall(
    payload: WindfallCreate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Windfall:
    windfall = Windfall(account_id=account.id, **payload.model_dump())
    db.add(windfall)
    await db.commit()
    await db.refresh(windfall)
    return windfall


@router.get("/export")
async def export_windfalls(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Response:
    result = await db.execute(select(Windfall).where(Windfall.account_id == account.id))
    csv_text = windfalls_to_csv(list(result.scalars().all()))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="windfalls-{account.id}.csv"'},
    )


def _describe_ambiguous_windfall(parsed: WindfallCreate, matches: list[Windfall]) -> str:
    return (
        f'"{parsed.name}" (${parsed.amount_cents / 100:.2f}, expected {parsed.expected_date}) '
        f"matches {len(matches)} existing windfalls - resolve manually before reimporting."
    )


@router.post("/import/preview", response_model=WindfallImportPreview)
async def preview_windfall_import(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> WindfallImportPreview:
    csv_text = (await file.read()).decode("utf-8-sig")  # -sig strips an Excel-added BOM
    parsed_windfalls, errors = parse_csv_rows(csv_text)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": [{"row": e.row, "message": e.message} for e in errors]},
        )

    result = await db.execute(select(Windfall).where(Windfall.account_id == account.id))
    existing_windfalls = list(result.scalars().all())
    reconciled = reconcile_windfalls(existing_windfalls, parsed_windfalls)

    return WindfallImportPreview(
        new=reconciled.new,
        updated=[
            WindfallImportUpdate(id=match.existing.id, fields=match.parsed)
            for match in reconciled.updated
        ],
        unchanged_count=len(reconciled.unchanged),
        ambiguous=[
            WindfallImportAmbiguous(message=_describe_ambiguous_windfall(a.parsed, a.matches))
            for a in reconciled.ambiguous
        ],
        omitted=[windfall for windfall in reconciled.omitted if windfall.enabled],
        errors=[],
    )


@router.post("/import/commit", response_model=WindfallImportCommitResponse)
async def commit_windfall_import(
    payload: WindfallImportCommitRequest,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> WindfallImportCommitResponse:
    created = [Windfall(account_id=account.id, **item.model_dump()) for item in payload.new]
    db.add_all(created)

    updated: list[Windfall] = []
    if payload.updated:
        ids = [item.id for item in payload.updated]
        result = await db.execute(
            select(Windfall).where(Windfall.id.in_(ids), Windfall.account_id == account.id)
        )
        windfalls_by_id = {windfall.id: windfall for windfall in result.scalars().all()}
        for item in payload.updated:
            windfall = windfalls_by_id.get(item.id)
            if windfall is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Windfall {item.id} not found"
                )
            for field, value in item.fields.model_dump().items():
                setattr(windfall, field, value)
            updated.append(windfall)

    disabled_count = 0
    if payload.omitted_ids:
        result = await db.execute(
            select(Windfall).where(
                Windfall.id.in_(payload.omitted_ids),
                Windfall.account_id == account.id,
                Windfall.enabled.is_(True),
            )
        )
        to_disable = list(result.scalars().all())
        for windfall in to_disable:
            windfall.enabled = False
        disabled_count = len(to_disable)

    await db.commit()
    for windfall in [*created, *updated]:
        await db.refresh(windfall)

    return WindfallImportCommitResponse(created=created, updated=updated, disabled_count=disabled_count)


@router.patch("/{windfall_id}", response_model=WindfallRead)
async def update_windfall(
    payload: WindfallUpdate,
    db: AsyncSession = Depends(get_db),
    windfall: Windfall = Depends(_get_owned_windfall),
    current_user: User = Depends(get_current_db_user),
) -> Windfall:
    update_data = payload.model_dump(exclude_unset=True)
    _reject_explicit_nulls(update_data)
    if "account_id" in update_data:
        # Moving to another account - the target must also belong to the
        # current user, same as get_owned_bank_account already validated for
        # the *current* account_id from the URL (mirrors Bill's move).
        await get_bank_account_or_404(update_data["account_id"], db, current_user)
    for field, value in update_data.items():
        setattr(windfall, field, value)
    await db.commit()
    await db.refresh(windfall)
    return windfall


@router.delete("/{windfall_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_windfall(
    db: AsyncSession = Depends(get_db),
    windfall: Windfall = Depends(_get_owned_windfall),
) -> None:
    await db.delete(windfall)
    await db.commit()
