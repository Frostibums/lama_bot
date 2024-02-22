import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DATE, BigInteger, Boolean

from database.db import Base


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)
    telegram_username = Column(String)
    registered_at = Column(DATE, default=datetime.date.today())


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    subscription_time = Column(Integer, nullable=False)  # in days
    price = Column(Integer, nullable=False)  # in dollars/USDT
    is_active = Column(Boolean, unique=False, default=True)


class TxnHash(Base):
    __tablename__ = "txn_hashs"

    id = Column(Integer, primary_key=True)
    chain = Column(String, nullable=False, default='TRON')
    transaction_hash = Column(String, nullable=False, unique=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    owner_telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'))
    subscription_plan_id = Column(BigInteger, ForeignKey('subscription_plans.id'))
    txn_hash_id = Column(Integer, ForeignKey('txn_hashs.id'))
    start_time = Column(DATE, default=datetime.date.today())
    end_time = Column(DATE, nullable=True)

