import datetime
import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import PAYMENT_WALLET
from bot.consts import STABLES_CONTRACTS
from bot.keyboards import get_main_keyboard, get_subscribe_plans_keyboard, get_subscribe_chain_keyboard
from bot.states import Subscription
from bot.texts import TextService
from bot.utils import check_payment_valid, send_notification
from database.services import (
    get_user_subscription_exp_date,
    get_active_plans,
    has_active_subscription,
    create_subscription,
    get_plan_by_id,
    get_chat_ids,
    scripts_sub_end_date
)

subscription_router = Router()
section = 'subscription'

logger = logging.getLogger('Subscriptios')


@subscription_router.message(F.text.lower() == "статус подписки")
async def check_subscription_status(message: Message) -> None:
    exp_date_chat = await get_user_subscription_exp_date(message.from_user.id)
    exp_date_scripts = await scripts_sub_end_date(message.from_user.id)
    msg = ''
    if exp_date_chat and exp_date_chat >= datetime.date.today():
        msg += f'Подписка заканчивается {exp_date_chat}\n'
    if exp_date_scripts and exp_date_scripts >= datetime.date.today():
        msg += f'Подписка на скрипты заканчивается {exp_date_scripts}\n'
    if not msg:
        await message.answer(
            TextService.get_text(section, 'has_no_sub'),
            reply_markup=await get_main_keyboard(telegram_id=message.from_user.id),
        )
    else:
        await message.answer(msg, reply_markup=await get_main_keyboard(telegram_id=message.from_user.id))


@subscription_router.message(F.text.lower() == "выбрать вариант")
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
    await callback.message.edit_text(
        f'Вы выбрали {token} в сети {chain}\n'
        f'Используемый адрес контракта: ||{contract_address}|| \n'
        f'Переводить сюда:\n`{PAYMENT_WALLET}`\n'
        f'Теперь отправьте хэш оплаты',
        parse_mode='MarkdownV2',
    )


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

    reply_msg = await message.reply(text=f'Проверяем...', reply_markup=await get_main_keyboard())
    if await check_payment_valid(plan_id, chain, token, txn_hash):
        subscription_plan = await get_plan_by_id(plan_id)
        try:
            msg_text = TextService.get_text(section, 'thank_for_sub')

            if not await has_active_subscription(tg_user.id):
                invite_links = [await message.bot.create_chat_invite_link(chat_id=chat_id, member_limit=1)
                                for chat_id in await get_chat_ids()]
                invite_links_to_show = '\n'.join([invite_link.invite_link for invite_link in invite_links])
                msg_text += f'\n\n{invite_links_to_show}'

            await create_subscription(
                telegram_id=tg_user.id,
                telegram_username=tg_user.username,
                chain=chain,
                transaction_hash=txn_hash,
                subscription_plan_id=plan_id
            )
            logger.info(f'{tg_user.username} ({tg_user.id}): {txn_hash} ({chain}) {plan_id=}')

            await message.answer(text=msg_text, reply_markup=await get_main_keyboard(telegram_id=message.from_user.id))
            await send_notification(
                message.bot,
                f'{message.from_user.username} ({message.from_user.id}) купил подписку'
                f' {subscription_plan.text} за {subscription_plan.price}$:\n `{txn_hash}` ({chain})'
            )

        except TelegramBadRequest as e:
            await message.answer(text=TextService.get_text(section, 'telegram_error'),
                                 reply_markup=await get_main_keyboard(telegram_id=message.from_user.id))
            await state.update_data(plan_id=None, chain=None, txn_hash=None)
            logger.error(str(e))
    else:
        await message.answer(
            text=TextService.get_text(section, 'bad_hash'),
            reply_markup=await get_main_keyboard(telegram_id=message.from_user.id),
        )

    await reply_msg.delete()
    await state.clear()
