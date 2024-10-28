from aiogram.fsm.state import StatesGroup, State


class Subscription(StatesGroup):
    plan_id = State()
    chain = State()
    token = State()
    txn_hash = State()


class InfoPage(StatesGroup):
    info_msg_id = State()
