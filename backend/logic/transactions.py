from typing import List

from backend.helpers.grouping import Grouping
from backend.models import (
    Transaction,
    TransactionRow,
    TransactionState,
    TransactionType,
)
from backend.models.interfaces import Database
from backend.models.models import BalanceItem, Blance


def transactions(db: Database, user_id: int) -> List[TransactionRow]:
    """
    Returns all transactions of a user.
    """
    return [
        transaction
        for transaction in db.scan("transactions")
        if transaction.user_id == user_id
    ]


def transaction(db: Database, user_id: int, transaction_id: int) -> TransactionRow:
    """
    Returns a given transaction of the user
    """
    transaction = db.get("transactions", transaction_id)
    return transaction if transaction and transaction.user_id == user_id else None


def create_transaction(
    db: Database, user_id: int, transaction: Transaction
) -> TransactionRow:
    """
    Creates a new transaction (adds an ID) and returns it.
    """
    if transaction.type in (TransactionType.DEPOSIT, TransactionType.REFUND):
        initial_state = TransactionState.PENDING
    elif transaction.type == TransactionType.SCHEDULED_WITHDRAWAL:
        initial_state = TransactionState.SCHEDULED
    else:
        raise ValueError(f"Invalid transaction type {transaction.type}")
    transaction_row = TransactionRow(
        user_id=user_id, **transaction.dict(), state=initial_state
    )
    return db.put("transactions", transaction_row)


def user_balance(db: Database, user_id: int) -> Blance:
    """
    Calculates the balance of a user and gives amount coverage information for each upcoming scheduled withdrawal
    """
    trxs = transactions(db, user_id)
    if len(trxs) == 0:
        return Blance(withdrawals=[], balance=0)

    grouping: Grouping[TransactionRow, str] = Grouping(trxs)
    grouping.group_by(lambda trx: f"{trx.type}-{trx.state}")

    scheduled_withdrawals = grouping.get_group(
        f"{TransactionType.SCHEDULED_WITHDRAWAL}-{TransactionState.SCHEDULED}"
    )
    completed_withdrawals = grouping.get_group(
        f"{TransactionType.SCHEDULED_WITHDRAWAL}-{TransactionState.COMPLETED}"
    )
    completed_deposits = grouping.get_group(
        f"{TransactionType.DEPOSIT}-{TransactionState.COMPLETED}"
    )
    completed_and_pending_refunds = grouping.get_group(
        f"{TransactionType.REFUND}-{TransactionState.COMPLETED}"
    ) + grouping.get_group(f"{TransactionType.REFUND}-{TransactionState.PENDING}")
    balance = (
        sum(trx.amount for trx in completed_deposits)
        - sum(trx.amount for trx in completed_withdrawals)
        - sum(trx.amount for trx in completed_and_pending_refunds)
    )

    scheduled_withdrawals = sorted(scheduled_withdrawals, key=lambda w: w.date)
    future_withdrawals: List[BalanceItem] = []
    for withdrawal in scheduled_withdrawals:
        amount = withdrawal.amount
        if amount == 0:  # ignore zero amounts
            continue
        if balance == 0:
            covered = 0
            covered_rate = 0
        else:
            # covered = amount if amount < balance else (amount - balance)
            covered = amount if amount < balance else balance
            covered_rate = round(100 * covered / amount)
            balance -= covered

        future_withdrawals.append(
            BalanceItem(
                amount=amount, covered_amount=covered, covered_rate=covered_rate
            )
        )

    return Blance(balance=balance, withdrawals=future_withdrawals)
