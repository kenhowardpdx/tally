from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_bank_account_or_404, get_current_db_user, get_owned_bank_account
from src.core.database import get_db
from src.models import BankAccount, Bill, Transaction, User
from src.schemas.transaction import (
    TransactionCreate,
    TransactionImportAmbiguous,
    TransactionImportCommitRequest,
    TransactionImportCommitResponse,
    TransactionImportPreview,
    TransactionImportRowIssue,
    TransactionImportUpdate,
    TransactionRead,
    TransactionUpdate,
)
from src.transactions_csv import parse_csv_rows, reconcile_transactions, transactions_to_csv

router = APIRouter(prefix="/api/v1/accounts/{account_id}/transactions", tags=["transactions"])


async def _get_owned_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Transaction:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.account_id == account.id
        )
    )
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


_NON_NULLABLE_UPDATE_FIELDS = ("amount_cents", "date")


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


async def _validate_bill_id(bill_id: int | None, account_id: int, db: AsyncSession) -> None:
    if bill_id is None:
        return
    result = await db.execute(select(Bill).where(Bill.id == bill_id, Bill.account_id == account_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.account_id == account.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Transaction:
    await _validate_bill_id(payload.bill_id, account.id, db)
    transaction = Transaction(account_id=account.id, **payload.model_dump())
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/export")
async def export_transactions(
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> Response:
    transactions_result = await db.execute(
        select(Transaction).where(Transaction.account_id == account.id)
    )
    bills_result = await db.execute(select(Bill).where(Bill.account_id == account.id))
    csv_text = transactions_to_csv(
        list(transactions_result.scalars().all()), list(bills_result.scalars().all())
    )
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="transactions-{account.id}.csv"'},
    )


def _describe_ambiguous_transaction(parsed: TransactionCreate) -> str:
    return (
        f"${parsed.amount_cents / 100:.2f} on {parsed.date}"
        f'{f" ({parsed.description})" if parsed.description else ""} matches more than one '
        "existing transaction - resolve manually before reimporting."
    )


@router.post("/import/preview", response_model=TransactionImportPreview)
async def preview_transaction_import(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> TransactionImportPreview:
    csv_text = (await file.read()).decode("utf-8-sig")  # -sig strips an Excel-added BOM
    bills_result = await db.execute(select(Bill).where(Bill.account_id == account.id))
    bills = list(bills_result.scalars().all())
    parsed_transactions, errors, warnings = parse_csv_rows(csv_text, bills)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": [{"row": e.row, "message": e.message} for e in errors]},
        )

    transactions_result = await db.execute(
        select(Transaction).where(Transaction.account_id == account.id)
    )
    existing_transactions = list(transactions_result.scalars().all())
    reconciled = reconcile_transactions(existing_transactions, parsed_transactions)

    return TransactionImportPreview(
        new=reconciled.new,
        updated=[
            TransactionImportUpdate(id=match.existing.id, fields=match.parsed)
            for match in reconciled.updated
        ],
        unchanged_count=len(reconciled.unchanged),
        ambiguous=[
            TransactionImportAmbiguous(message=_describe_ambiguous_transaction(a.parsed))
            for a in reconciled.ambiguous
        ],
        omitted=reconciled.omitted,
        warnings=[TransactionImportRowIssue(row=w.row, message=w.message) for w in warnings],
        errors=[],
    )


@router.post("/import/commit", response_model=TransactionImportCommitResponse)
async def commit_transaction_import(
    payload: TransactionImportCommitRequest,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
) -> TransactionImportCommitResponse:
    for item in payload.new:
        await _validate_bill_id(item.bill_id, account.id, db)
    for item in payload.updated:
        await _validate_bill_id(item.fields.bill_id, account.id, db)

    created = [Transaction(account_id=account.id, **item.model_dump()) for item in payload.new]
    db.add_all(created)

    updated: list[Transaction] = []
    if payload.updated:
        ids = [item.id for item in payload.updated]
        result = await db.execute(
            select(Transaction).where(Transaction.id.in_(ids), Transaction.account_id == account.id)
        )
        transactions_by_id = {transaction.id: transaction for transaction in result.scalars().all()}
        for item in payload.updated:
            transaction = transactions_by_id.get(item.id)
            if transaction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction {item.id} not found"
                )
            for field, value in item.fields.model_dump().items():
                setattr(transaction, field, value)
            updated.append(transaction)

    deleted_count = 0
    if payload.omitted_ids:
        result = await db.execute(
            select(Transaction).where(
                Transaction.id.in_(payload.omitted_ids), Transaction.account_id == account.id
            )
        )
        to_delete = list(result.scalars().all())
        for transaction in to_delete:
            await db.delete(transaction)
        deleted_count = len(to_delete)

    await db.commit()
    for transaction in [*created, *updated]:
        await db.refresh(transaction)

    return TransactionImportCommitResponse(created=created, updated=updated, deleted_count=deleted_count)


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    payload: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    account: BankAccount = Depends(get_owned_bank_account),
    transaction: Transaction = Depends(_get_owned_transaction),
    current_user: User = Depends(get_current_db_user),
) -> Transaction:
    update_data = payload.model_dump(exclude_unset=True)
    _reject_explicit_nulls(update_data)
    if "account_id" in update_data:
        # Moving to another account - the target must also belong to the
        # current user, same as get_owned_bank_account already validated for
        # the *current* account_id from the URL (mirrors Bill's move).
        await get_bank_account_or_404(update_data["account_id"], db, current_user)
    if "bill_id" in update_data:
        await _validate_bill_id(update_data["bill_id"], account.id, db)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    db: AsyncSession = Depends(get_db),
    transaction: Transaction = Depends(_get_owned_transaction),
) -> None:
    await db.delete(transaction)
    await db.commit()
