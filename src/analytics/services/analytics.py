from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.transactions.enums import TransactionStatusEnum
from src.transactions.models import Transaction
from src.users.enums import CurrencyEnum
from src.users.models import User
from src.utils.utils import utc_now


EXCHANGE_RATES_TO_USD: dict[CurrencyEnum, float] = {
    CurrencyEnum.USD: 1,
    CurrencyEnum.EUR: 0.9342,
    CurrencyEnum.AUD: 0.5447,
    CurrencyEnum.CAD: 0.6162,
    CurrencyEnum.ARS: 0.0009,
    CurrencyEnum.PLN: 0.2343,
    CurrencyEnum.BTC: 100000.0,
    CurrencyEnum.ETH: 3557.3476,
    CurrencyEnum.DOGE: 0.3627,
    CurrencyEnum.USDT: 0.9709,
}


class AnalyticsService:
    def __init__(self) -> None:
        self.exchange_rates: dict[CurrencyEnum, float] = EXCHANGE_RATES_TO_USD

    async def generate_weekly_reports(self, session: AsyncSession, weeks_count: int = 52) -> list[dict[str, Any]]:
        today = utc_now().date()
        oldest_date = today - timedelta(weeks=weeks_count - 1, days=6)

        users_query = select(User.id, User.created).where(User.created >= oldest_date)
        users_result = await session.execute(users_query)
        all_users = [(row.id, row.created.date()) for row in users_result]

        transactions_query = select(
            Transaction.user_id, Transaction.amount, Transaction.status, Transaction.currency, Transaction.created
        ).where(Transaction.created >= oldest_date)
        transactions_result = await session.execute(transactions_query)
        all_transactions: list[dict[str, Any]] = [
            {
                "user_id": row.user_id,
                "amount": float(row.amount),
                "status": row.status,
                "currency": row.currency,
                "created": row.created.date(),
            }
            for row in transactions_result
        ]

        reports: list[dict[str, Any]] = []

        for week_offset in range(weeks_count):
            week_end = today - timedelta(weeks=week_offset)
            week_start = week_end - timedelta(days=6)

            report: dict[str, Any] = await self._generate_single_week_report(
                week_start, week_end, all_users, all_transactions
            )
            reports.append(report)

        reports.sort(key=lambda x: x["week_start"])

        return reports

    async def _generate_single_week_report(
        self, week_start: date, week_end: date, all_users: list[tuple[Any, ...]], all_transactions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate report for single week"""
        week_users = [user_id for user_id, created in all_users if week_start <= created <= week_end]
        week_user_ids = set(week_users)
        week_transactions = [
            transaction for transaction in all_transactions if week_start <= transaction["created"] <= week_end
        ]

        new_users_count = len(week_users)

        deposit_user_ids = {transaction["user_id"] for transaction in week_transactions if transaction["amount"] > 0}
        users_with_deposit_count = len(week_user_ids & deposit_user_ids)

        deposit_amount = sum(
            transaction["amount"] * self.exchange_rates.get(transaction["currency"], 1.0)
            for transaction in week_transactions
            if transaction["amount"] > 0 and transaction["status"] != TransactionStatusEnum.ROLL_BACKED
        )

        withdraw_amount = sum(
            abs(transaction["amount"]) * self.exchange_rates.get(transaction["currency"], 1.0)
            for transaction in week_transactions
            if transaction["amount"] < 0 and transaction["status"] != TransactionStatusEnum.ROLL_BACKED
        )

        total_transactions_count = len(week_transactions)

        non_rollbacked_transactions_count = len(
            [
                transaction
                for transaction in week_transactions
                if transaction["status"] != TransactionStatusEnum.ROLL_BACKED
            ]
        )

        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "new_users_count": new_users_count,
            "users_with_deposit_count": users_with_deposit_count,
            "deposit_amount_usd": round(deposit_amount, 2),
            "withdraw_amount_usd": round(withdraw_amount, 2),
            "total_transactions_count": total_transactions_count,
            "non_rollbacked_transactions_count": non_rollbacked_transactions_count,
        }
