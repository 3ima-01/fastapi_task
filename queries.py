from datetime import date

from sqlalchemy import Date, and_, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.transactions.models import Transaction
from src.users.enums import CurrencyEnum
from src.users.models import User

EXCHANGE_RATES_TO_USD = {
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


async def get_registered_users_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
    """Количество зарегистрированных пользователей за период"""
    q = select(func.count(User.id)).where(and_(cast(User.created, Date) >= dt_gt, cast(User.created, Date) <= dt_lt))
    result = await session.execute(q)
    return result.scalar() or 0


async def get_registered_and_deposit_users_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
    """Количество пользователей, которые зарегистрировались И внесли депозит за период"""
    q = (
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(
            Transaction,
            and_(
                Transaction.user_id == User.id,
                Transaction.amount > 0,
                cast(Transaction.created, Date) >= dt_gt,
                cast(Transaction.created, Date) <= dt_lt,
            ),
        )
        .where(and_(cast(User.created, Date) >= dt_gt, cast(User.created, Date) <= dt_lt))
    )
    result = await session.execute(q)
    return result.scalar() or 0


async def get_registered_and_not_rollbacked_deposit_users_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
    """Количество пользователей с неоткаченными депозитами"""
    q = (
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(
            Transaction,
            and_(
                Transaction.user_id == User.id,
                Transaction.amount > 0,
                Transaction.status != "ROLLBACKED",
                cast(Transaction.created, Date) >= dt_gt,
                cast(Transaction.created, Date) <= dt_lt,
            ),
        )
        .where(and_(cast(User.created, Date) >= dt_gt, cast(User.created, Date) <= dt_lt))
    )
    result = await session.execute(q)
    return result.scalar() or 0


async def get_not_rollbacked_deposit_amount(session: AsyncSession, dt_gt: date, dt_lt: date) -> float:
    """Сумма неоткаченных депозитов в USD"""
    q = select(
        func.sum(
            Transaction.amount
            * func.coalesce(
                case(
                    *[(Transaction.currency == currency, rate) for currency, rate in EXCHANGE_RATES_TO_USD.items()],
                    else_=1.0,
                ),
                1.0,
            )
        )
    ).where(
        and_(
            Transaction.amount > 0,
            Transaction.status != "ROLLBACKED",
            cast(Transaction.created, Date) >= dt_gt,
            cast(Transaction.created, Date) <= dt_lt,
        )
    )
    result = await session.execute(q)
    amount = result.scalar() or 0
    return float(amount) if amount else 0.0


async def get_not_rollbacked_withdraw_amount(session: AsyncSession, dt_gt: date, dt_lt: date) -> float:
    """Сумма неоткаченных выводов в USD (положительное число)"""
    q = select(
        func.sum(
            func.abs(Transaction.amount)  # Берем абсолютное значение
            * func.coalesce(
                case(
                    *[(Transaction.currency == currency, rate) for currency, rate in EXCHANGE_RATES_TO_USD.items()],
                    else_=1.0,
                ),
                1.0,
            )
        )
    ).where(
        and_(
            Transaction.amount < 0,  # Выводы отрицательные
            Transaction.status != "ROLLBACKED",
            cast(Transaction.created, Date) >= dt_gt,
            cast(Transaction.created, Date) <= dt_lt,
        )
    )
    result = await session.execute(q)
    amount = result.scalar() or 0
    return float(amount) if amount else 0.0


async def get_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
    """Общее количество транзакций за период"""
    q = select(func.count(Transaction.id)).where(
        and_(cast(Transaction.created, Date) >= dt_gt, cast(Transaction.created, Date) <= dt_lt)
    )
    result = await session.execute(q)
    return result.scalar() or 0


async def get_not_rollbacked_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date) -> int:
    """Количество неоткаченных транзакций за период"""
    q = select(func.count(Transaction.id)).where(
        and_(
            Transaction.status != "ROLLBACKED",
            cast(Transaction.created, Date) >= dt_gt,
            cast(Transaction.created, Date) <= dt_lt,
        )
    )
    result = await session.execute(q)
    return result.scalar() or 0
