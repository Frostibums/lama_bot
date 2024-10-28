import datetime

from sqlalchemy import select, func

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


async def get_user_subscription_exp_date(telegram_id):
    async with async_session() as session:
        query = select(func.max(Subscription.end_time)).filter_by(owner_telegram_id=telegram_id)
        query_result = await session.execute(query)
        exp_date = query_result.first()
        return exp_date[0] if exp_date else None


async def has_active_subscription(telegram_id):
    exp_date = await get_user_subscription_exp_date(telegram_id)
    if not exp_date:
        return False
    return exp_date >= datetime.date.today()


async def create_subscription(telegram_id,
                              telegram_username,
                              chain,
                              transaction_hash,
                              subscription_plan_id):
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
            end_time=end_time
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


async def create_subscription_plan(subscription_time, price):
    async with async_session() as session:
        new_plan = SubscriptionPlan(subscription_time=subscription_time, price=price)
        session.add(new_plan)
        await session.commit()
        return new_plan


async def get_tg_ids_to_notify_by_exp_date(exp_date: datetime.date) -> list[int]:
    async with async_session() as session:
        query = select(Subscription.owner_telegram_id).where(Subscription.end_time == exp_date)
        query_result = await session.execute(query)
        tg_ids = [tg_id[0] for tg_id in query_result.all()
                  if await get_user_subscription_exp_date(tg_id[0]) <= exp_date]
        return tg_ids or []


async def get_tg_ids_to_kick_by_exp_date(exp_date: datetime.date) -> list[int]:
    async with async_session() as session:
        query = select(Subscription.owner_telegram_id).where(Subscription.end_time <= exp_date)
        query_result = await session.execute(query)
        tg_ids = [tg_id[0] for tg_id in query_result.all()
                  if await get_user_subscription_exp_date(tg_id[0]) <= exp_date]
        return tg_ids or []

# async def get_sub_users_info():
#     async with async_session() as session:
#         query = select(
#             User.telegram_id, User.telegram_username, User.registered_at, func.max(Subscription.end_time).label('end_time')
#         ).join(
#             Subscription, User.telegram_id == Subscription.owner_telegram_id
#         ).group_by(User.telegram_id, Subscription.owner_telegram_id)
#
#         query_result = await session.execute(query)
#         return query_result.all()


async def get_active_plans() -> list[SubscriptionPlan]:
    async with async_session() as session:
        query = select(SubscriptionPlan).filter_by(is_active=True)
        query_result = await session.execute(query)
        return [plan[0] for plan in query_result.all()] if query_result else []


async def get_plans() -> list[SubscriptionPlan]:
    async with async_session() as session:
        query = select(SubscriptionPlan)
        query_result = await session.execute(query)
        return [plan[0] for plan in query_result.all()] if query_result else []
