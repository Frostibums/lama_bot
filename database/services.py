import asyncio
import datetime
import logging
from typing import cast

from sqlalchemy import select, func, update, exists, or_

from bot.config import group_chat_ids, group_2_chat_ids
from database.db import async_session
from database.models import User, SubscriptionPlan, TxnHash, Subscription


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


async def get_user_subscription_exp_date(telegram_id, subscr_lvl: int = 1):
    async with async_session() as session:
        query = (
            select(func.max(Subscription.end_time))
            .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
            .where(Subscription.owner_telegram_id == telegram_id, SubscriptionPlan.level == subscr_lvl)
        )
        query_result = await session.execute(query)
        exp_date = query_result.first()
        return exp_date[0] if exp_date else None


async def has_active_subscription(telegram_id, subscr_lvl: int = 1):
    exp_date = await get_user_subscription_exp_date(telegram_id, subscr_lvl)
    if not exp_date:
        return False
    return exp_date >= datetime.date.today()


async def give_sub(
        telegram_id: int,
        telegram_username: str,
        end_date: datetime.date,
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

        return True


async def get_transaction_hash(transaction_hash):
    async with async_session() as session:
        query = select(TxnHash).filter_by(transaction_hash=transaction_hash)
        query_result = await session.execute(query)
        txn_hash = query_result.first()
    return txn_hash[0] if txn_hash else None


async def create_subscription_plan(subscription_time, price, level, text):
    async with async_session() as session:
        new_plan = SubscriptionPlan(subscription_time=subscription_time, price=price, level=level, text=text)
        session.add(new_plan)
        await session.commit()
        return new_plan


async def get_tg_ids_to_notify_by_exp_date(exp_date: datetime.date, level: int = 1) -> list[int]:
    async with async_session() as session:
        query = (
            select(Subscription.owner_telegram_id)
            .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
            .where(Subscription.end_time == exp_date, SubscriptionPlan.level == level)
        )
        query_result = await session.scalars(query)
        tg_ids = []
        for tg_id in query_result:
            end_date = await get_user_subscription_exp_date(tg_id, level)
            if end_date and end_date <= exp_date:
                tg_ids.append(tg_id)
        return tg_ids


async def get_tg_ids_to_kick_by_exp_date(exp_date: datetime.date, level: int = 1) -> list[int]:
    async with async_session() as session:
        query = select(Subscription.owner_telegram_id).where(Subscription.end_time <= exp_date).filter_by(level=level)
        query_result = await session.execute(query)
        tg_ids = [tg_id[0] for tg_id in query_result.all()
                  if await get_user_subscription_exp_date(tg_id[0], level) <= exp_date]
        return tg_ids or []

def testt():
    date = datetime.date.fromisoformat('2025-01-31')
    r1 = asyncio.run(get_users_to_kick_by_exp_date(date, 1))
    r2 = asyncio.run(get_users_to_kick_by_exp_date(date, 2))
    r3 = asyncio.run(get_downgraded_users(date))
    print([r.telegram_username for r in r1])
    print([r.telegram_username for r in r2])
    print([r.telegram_username for r in r3])


async def get_users_to_kick_by_exp_date(exp_date: datetime.date, level: int = 1) -> list[User]:
    query = (
        select(User)
        .join(Subscription, User.telegram_id == Subscription.owner_telegram_id)
        .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
        .where(or_(SubscriptionPlan.level == level, SubscriptionPlan.level == None))
        .having(func.max(Subscription.end_time) <= exp_date)
        .group_by(User.telegram_id)
    )

    if level == 1:
        query = query.where(~Subscription.owner_telegram_id.in_(
                select(Subscription.owner_telegram_id)
                .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
                .where(SubscriptionPlan.level == 2)
                .where(Subscription.end_time > exp_date)
            )
        )
    if level == 2:
        query = query.where(~Subscription.owner_telegram_id.in_(
                select(Subscription.owner_telegram_id)
                .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
                .where(SubscriptionPlan.level == 1)
                .where(Subscription.end_time > exp_date)
            )
        )

    async with async_session() as session:
        return await session.scalars(query)


async def get_downgraded_users(exp_date: datetime.date) -> list[User]:
    query = (
        select(User)
        .join(Subscription, User.telegram_id == Subscription.owner_telegram_id)
        .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
        .where(SubscriptionPlan.level == 2)
        .having(func.max(Subscription.end_time) <= exp_date)
        .where(Subscription.owner_telegram_id.in_(
                select(Subscription.owner_telegram_id)
                .join(SubscriptionPlan, Subscription.subscription_plan_id == SubscriptionPlan.id)
                .where(SubscriptionPlan.level == 1)
                .where(Subscription.end_time > exp_date)
            )
        )
        .group_by(User.telegram_id)
    )
    async with async_session() as session:
        return await session.scalars(query)


async def get_sub_users_info():
    async with async_session() as session:
        query = select(
            User.telegram_id,
            User.telegram_username,
            User.registered_at,
            func.max(Subscription.end_time).label('end_time')
        ).join(
            Subscription, User.telegram_id == Subscription.owner_telegram_id
        ).group_by(User.telegram_id, User.telegram_username, User.registered_at)

        query_result = await session.execute(query)
        return query_result.fetchall()


async def get_active_plans() -> list[SubscriptionPlan]:
    async with async_session() as session:
        query = select(SubscriptionPlan).filter_by(is_active=True)
        query_result = await session.execute(query)
        return [plan[0] for plan in query_result.all()] if query_result else []


async def get_plans() -> list[SubscriptionPlan]:
    async with async_session() as session:
        return await session.scalars(select(SubscriptionPlan))


async def update_plan_activity(plan_id: int, active: bool) -> None:
    async with async_session() as session:
        stmt = update(SubscriptionPlan).where(
            cast('ColumnElement[bool]', SubscriptionPlan.id == plan_id)
        ).values(is_active=active)
        await session.execute(stmt)
        await session.commit()


async def get_plan_chats_by_lvl(level: int) -> list[str]:
    if level == 1:
        return group_chat_ids
    if level == 2:
        return group_chat_ids + group_2_chat_ids
    raise ValueError
