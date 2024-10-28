import datetime

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import group_chat_ids, PAYMENT_WALLET
from bot.consts import STABLES_CONTRACTS
from bot.keyboards import get_main_keyboard, get_subscribe_plans_keyboard, get_subscribe_chain_keyboard
from bot.states import Subscription
from bot.texts import TextService
from bot.utils import check_payment_valid
from database.services import (get_user_subscription_exp_date,
                               get_active_plans,
                               has_active_subscription,
                               create_subscription)


subscription_router = Router()
section = 'subscription'


@subscription_router.message(F.text.lower() == "проверить статус подписки")
async def check_subscription_status(message: Message) -> None:
    exp_date = await get_user_subscription_exp_date(message.from_user.id)
    if not exp_date or exp_date < datetime.date.today():
        await message.answer(TextService.get_text(section, 'has_no_sub'), reply_markup=get_main_keyboard())
    else:
        await message.answer(f'Ваша подписка заканчивается {exp_date}!', reply_markup=get_main_keyboard())


@subscription_router.message(F.text.lower() == "купить подписку")
async def buy_subscription(message: Message, state: FSMContext) -> None:
    await state.update_data(plan_id=None, chain=None, txn_hash=None)
    active_plans = await get_active_plans()
    await state.set_state(Subscription.plan_id)
    await message.answer(TextService.get_text(section, 'subscription_plans'),
                         reply_markup=get_subscribe_plans_keyboard(active_plans),
                         parse_mode='Markdown')


@subscription_router.callback_query(Subscription.plan_id, F.data.contains('subscription_'))
async def create_payment(callback: CallbackQuery, state: FSMContext) -> None:
    plan_id = callback.data.split('_')[1]
    await state.update_data(plan_id=plan_id)
    await state.set_state(Subscription.chain)
    await callback.message.edit_text(TextService.get_text(section, 'ask_chain'),
                                     parse_mode='Markdown',
                                     reply_markup=get_subscribe_chain_keyboard())


@subscription_router.callback_query(Subscription.chain)
async def process_chain(callback: CallbackQuery, state: FSMContext) -> None:
    cb_data = callback.data.split('_')
    chain = cb_data[1].lower()
    token = cb_data[2].lower()
    await state.update_data(chain=chain.lower())
    await state.update_data(token=token.lower())
    await state.set_state(Subscription.txn_hash)
    contract_address = STABLES_CONTRACTS.get(token).get(chain)
    await callback.message.edit_text(f'Вы выбрали {token} в сети {chain}\n'
                                     f'Используемый адрес контракта: {contract_address}\n'
                                     f'Переводить сюда: {PAYMENT_WALLET}\n'
                                     f'Теперь отправьте хэш оплаты!')


@subscription_router.message(Subscription.txn_hash)
async def process_hash(message: Message, state: FSMContext) -> None:
    data = await state.update_data(txn_hash=message.text.lower())
    try:
        plan_id = int(data.get('plan_id'))
    except TypeError as e:
        await state.update_data(plan_id=None, chain=None, txn_hash=None)
        return
    chain = data.get('chain')
    token = data.get('token')
    txn_hash = data.get('txn_hash')
    tg_user = message.from_user

    reply_msg = await message.reply(text=f'Проверяем...', reply_markup=get_main_keyboard())
    if await check_payment_valid(plan_id, chain, token, txn_hash):
        try:
            msg_text = TextService.get_text(section, 'thank_for_sub')
            if not await has_active_subscription(tg_user.id):
                invite_links = [await message.bot.create_chat_invite_link(chat_id=chat_id, member_limit=1)
                                for chat_id in group_chat_ids]
                invite_links_to_show = '\n'.join([invite_link.invite_link for invite_link in invite_links])
                msg_text += f'\n\n{invite_links_to_show}'

            await create_subscription(
                telegram_id=tg_user.id,
                telegram_username=tg_user.username,
                chain=chain,
                transaction_hash=txn_hash,
                subscription_plan_id=plan_id
            )

            await message.answer(text=msg_text, reply_markup=get_main_keyboard())

        except TelegramBadRequest:
            await message.answer(text=TextService.get_text(section, 'telegram_error'),
                                 reply_markup=get_main_keyboard())

    else:
        await message.answer(text=TextService.get_text(section, 'bad_hash'),
                             reply_markup=get_main_keyboard())

    await reply_msg.delete()
    await state.update_data(plan_id=None, chain=None, txn_hash=None)
