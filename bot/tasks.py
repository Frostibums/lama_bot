import asyncio
import datetime

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from bot.texts import TextService
from bot.utils import send_notification
from celery_beat import celery_app
from database.services import get_tg_ids_to_notify_by_exp_date, get_tg_ids_to_kick_by_exp_date
from bot.bot_tg import tg_bot
from bot.config import group_chat_ids


async def kick_user_from_group(chat_id, user_tg_id) -> bool:
    try:
        member = await tg_bot.get_chat_member(chat_id=chat_id, user_id=int(user_tg_id))
    except TelegramBadRequest:
        return False
    if member.status != ChatMemberStatus.MEMBER:
        return False
    try:
        await tg_bot.ban_chat_member(chat_id=chat_id, user_id=user_tg_id)
        await tg_bot.unban_chat_member(chat_id=chat_id, user_id=user_tg_id)
        return True
    except Exception as e:
        return False


async def async_notify_about_subscription_expiration():
    delta_days = 3
    today = datetime.date.today()

    telegram_ids_to_notify = set(await get_tg_ids_to_notify_by_exp_date(today + datetime.timedelta(days=delta_days)))
    for telegram_id in telegram_ids_to_notify:
        try:
            await tg_bot.send_message(telegram_id, TextService.get_text('subscription', 'expiration'))
        except Exception as e:
            continue

    telegram_ids_expired = set()
    for i in range(1, delta_days + 1):
        telegram_ids_expired.union(await get_tg_ids_to_notify_by_exp_date(today - datetime.timedelta(days=i)))

    for telegram_id in telegram_ids_expired:
        try:
            await tg_bot.send_message(telegram_id, TextService.get_text('subscription', 'expired'))
        except Exception as e:
            continue

    return True


async def async_kick_users_with_exp_sub():
    delta_days = 3
    kick_day = datetime.date.today() - datetime.timedelta(days=delta_days)
    telegram_ids_to_kick = await get_tg_ids_to_kick_by_exp_date(kick_day)
    for telegram_id in telegram_ids_to_kick:
        for chat_id in group_chat_ids:
            try:
                if await kick_user_from_group(chat_id, telegram_id):
                    await send_notification(
                        tg_bot,
                        f'Кикнут telegram id: `{telegram_id}`',
                    )
                await asyncio.sleep(1)
            except Exception as e:
                continue
    return True


@celery_app.task(autostart=False)
def notify_about_subscription_expiration():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_notify_about_subscription_expiration())


@celery_app.task(autostart=False)
def kick_users_with_exp_sub():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_kick_users_with_exp_sub())
