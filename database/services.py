import datetime
from typing import cast

from sqlalchemy import select, func, update

from bot.config import group_chat_ids
from database.db import async_session
from database.models import User, SubscriptionPlan, TxnHash, Subscription, ScriptsSubscription


async def create_user(telegram_id, telegram_username):
    async with async_session() as session:
        new_user = User(telegram_id=telegram_id, telegram_username=telegram_username)
        session.add(new_user)
        await session.commit()
        return new_user


async def get_user_by_telegram_id(telegram_id):
    async with async_session() as session:
        query = select(User).filter_by(telegram_id=telegram_id)
        query_result = await session.execute(query)
        user = query_result.first()
        return user[0] if user else None


async def get_plan_by_id(plan_id) -> SubscriptionPlan | None:
    async with async_session() as session:
        query = select(SubscriptionPlan).filter_by(id=plan_id)
        query_result = await session.execute(query)
        plan = query_result.first()
        return plan[0] if plan else None


async def get_plan_price_by_id(plan_id):
    plan = await get_plan_by_id(int(plan_id))
    return plan.price if plan else None


async def get_user_subscription_exp_date(telegram_id: int) -> datetime.date:
    query = (
        select(func.max(Subscription.end_time))
        .where(Subscription.owner_telegram_id == telegram_id)
    )
    async with async_session() as session:
        return await session.scalar(query)


async def has_active_subscription(telegram_id: int) -> bool:
    exp_date = await get_user_subscription_exp_date(telegram_id)
    if not exp_date:
        return False
    return exp_date >= datetime.date.today()


async def give_sub(
        telegram_id: int,
        telegram_username: str,
        end_date: datetime.date,
        scripts_allowance: bool = False,
) -> bool:
    async with async_session() as session:
        user = await get_user_by_telegram_id(telegram_id)
        if not user:
            user = await create_user(telegram_id=telegram_id, telegram_username=telegram_username)

        subscription = Subscription(
            owner_telegram_id=user.telegram_id,
            end_time=end_date,
        )
        session.add(subscription)

        if scripts_allowance:
            await create_scripts_subscription(
                telegram_id=user.telegram_id,
                end_time=end_date,
            )

        await session.commit()

        return True


async def create_subscription(
        telegram_id,
        telegram_username,
        chain,
        transaction_hash,
        subscription_plan_id,
):
    async with async_session() as session:
        user = await get_user_by_telegram_id(telegram_id)
        plan = await get_plan_by_id(subscription_plan_id)
        delta = datetime.timedelta(days=plan.subscription_time + 1)

        if not user:
            user = await create_user(telegram_id=telegram_id, telegram_username=telegram_username)

        exp_date = await get_user_subscription_exp_date(telegram_id)
        if not exp_date or exp_date < datetime.date.today():
            end_time = datetime.date.today() + delta
        else:
            end_time = exp_date + delta

        new_hash = TxnHash(
            chain=chain,
            transaction_hash=transaction_hash
        )
        session.add(new_hash)
        await session.commit()

        subscription = Subscription(
            owner_telegram_id=user.telegram_id,
            subscription_plan_id=subscription_plan_id,
            txn_hash_id=new_hash.id,
            end_time=end_time,
        )
        session.add(subscription)
        await session.commit()

        if plan.level > 1:
            await create_scripts_subscription(
                telegram_id=user.telegram_id,
                end_time=datetime.date.today() + delta,
            )

        return True


async def get_transaction_hash(transaction_hash):
    async with async_session() as session:
        query = select(TxnHash).filter_by(transaction_hash=transaction_hash)
        query_result = await session.execute(query)
        txn_hash = query_result.first()
    return txn_hash[0] if txn_hash else None


async def create_scripts_subscription(telegram_id: int, end_time: datetime.date) -> ScriptsSubscription:
    new_scripts_sub = ScriptsSubscription(
        owner_telegram_id=telegram_id,
        end_time=end_time,
    )
    async with async_session() as session:
        session.add(new_scripts_sub)
        await session.commit()
        return new_scripts_sub


async def scripts_sub_end_date(telegram_id: int) -> datetime.date:
    async with async_session() as session:
        return await session.scalar(
            select(func.max(ScriptsSubscription.end_time))
            .where(ScriptsSubscription.owner_telegram_id == telegram_id)
        )


async def has_scripts_sub(telegram_id: int, by_date: datetime.date | None = None) -> bool:
    end_date = await scripts_sub_end_date(telegram_id)
    if not end_date:
        return False
    by_date = by_date or datetime.date.today()
    return end_date >= by_date


async def create_subscription_plan(subscription_time, price, level, text):
    async with async_session() as session:
        new_plan = SubscriptionPlan(subscription_time=subscription_time, price=price, level=level, text=text)
        session.add(new_plan)
        await session.commit()
        return new_plan


async def get_tg_ids_to_notify_by_exp_date(exp_date: datetime.date) -> list[int]:
    query = (
        select(Subscription.owner_telegram_id)
        .group_by(Subscription.owner_telegram_id)
        .having(func.max(Subscription.end_time) == exp_date)
    )
    async with async_session() as session:
        return await session.scalars(query) or []


async def get_users_to_kick_by_exp_date(exp_date: datetime.date) -> list[User]:
    query = (
        select(User)
        .join(Subscription, User.telegram_id == Subscription.owner_telegram_id)
        .group_by(User)
        .having(func.max(Subscription.end_time) <= exp_date)
    )
    async with async_session() as session:
        return await session.scalars(query) or []


async def get_sub_users_info(is_full: bool = False):
    query = select(
        User.telegram_id,
        User.telegram_username,
        User.registered_at,
        func.max(Subscription.end_time).label('end_time'),
        func.max(ScriptsSubscription.end_time).label('scripts_end_time'),
    ).join(
        Subscription, User.telegram_id == Subscription.owner_telegram_id
    ).join(
        ScriptsSubscription, User.telegram_id == ScriptsSubscription.owner_telegram_id, isouter=True
    ).group_by(
        User.telegram_id
    ).order_by(
        func.max(Subscription.end_time).desc()
    )
    if not is_full:
        query = query.having(
            func.max(Subscription.end_time) >= datetime.date.today() - datetime.timedelta(days=5)
        )
    async with async_session() as session:
        query_result = await session.execute(query)
        return query_result.fetchall()


async def edit_user_sub_end_time(user_id: int, new_end_time: datetime.date) -> User | None:
    query = update(
        Subscription
    ).where(
        Subscription.owner_telegram_id == user_id,
        Subscription.end_time >= datetime.date.today() - datetime.timedelta(days=5),
    ).values(
        end_time=new_end_time
    )
    async with async_session() as session:
        await session.execute(query)
        await session.commit()
        return await session.scalar(select(User).where(User.telegram_id == user_id))


async def edit_user_scripts_sub_end_time(user_id: int, new_end_time: datetime.date) -> User | None:
    query = update(
        ScriptsSubscription
    ).where(
        ScriptsSubscription.owner_telegram_id == user_id,
        ScriptsSubscription.end_time >= datetime.date.today() - datetime.timedelta(days=5),
    ).values(
        end_time=new_end_time
    )

    async with async_session() as session:
        await session.execute(query)
        await session.commit()
        return await session.scalar(select(User).where(User.telegram_id == user_id))


async def get_active_plans() -> list[SubscriptionPlan]:
    query = select(SubscriptionPlan).filter_by(is_active=True)
    async with async_session() as session:
        return await session.scalars(query)


async def get_plans() -> list[SubscriptionPlan]:
    async with async_session() as session:
        return await session.scalars(select(SubscriptionPlan))


async def update_plan_activity(plan_id: int, active: bool) -> None:
    stmt = update(SubscriptionPlan).where(
        cast('ColumnElement[bool]', SubscriptionPlan.id == plan_id)
    ).values(is_active=active)
    async with async_session() as session:
        await session.execute(stmt)
        await session.commit()


async def get_chat_ids() -> list[str]:
    return group_chat_ids
