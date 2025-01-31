import asyncio
import datetime
import logging

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from bot.texts import TextService
from bot.utils import send_notification
from celery_beat import celery_app
from database.services import get_tg_ids_to_notify_by_exp_date, get_users_to_kick_by_exp_date, get_downgraded_users
from bot.bot_tg import tg_bot
from bot.config import group_chat_ids, group_2_chat_ids


logger = logging.getLogger('kick_notify')


async def kick_user_from_group(chat_id, user_tg_id: int) -> bool:
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

    telegram_ids_to_notify_1 = set(
        await get_tg_ids_to_notify_by_exp_date(today + datetime.timedelta(days=delta_days), level=1)
    )
    telegram_ids_to_notify_2 = set(
        await get_tg_ids_to_notify_by_exp_date(today + datetime.timedelta(days=delta_days), level=2)
    )

    for telegram_id in telegram_ids_to_notify_1.union(telegram_ids_to_notify_2):
        try:
            await tg_bot.send_message(telegram_id, TextService.get_text('subscription', 'expiration'))
        except Exception as e:
            continue

    telegram_ids_expired = set()
    for i in range(0, delta_days + 1):
        for level in (1, 2):
            telegram_ids_expired = telegram_ids_expired.union(await get_tg_ids_to_notify_by_exp_date(
                today - datetime.timedelta(days=i),
                level,
            ))
    for telegram_id in telegram_ids_expired:
        try:
            await tg_bot.send_message(telegram_id, TextService.get_text('subscription', 'expired'))
        except Exception as e:
            continue

    return True


async def async_kick_users_with_exp_sub():
    delta_days = 3
    kick_day = datetime.date.today() - datetime.timedelta(days=delta_days)

    kicking_lvl1 = list(await get_users_to_kick_by_exp_date(kick_day, level=1))  # кикаем из первой группы (кончилась первая и нет второй)
    kicking_both = list(await get_users_to_kick_by_exp_date(kick_day, level=2))  # кикаем из обеих групп (кончилась вторая и нет первой)
    downgrade = list(await get_downgraded_users(kick_day))  # кикаем только со второй группы (кончилась вторая, есть первая)

    kicked = []
    for u in kicking_lvl1 + kicking_both:
        for chat_id in group_chat_ids:
            try:
                if await kick_user_from_group(chat_id, u.telegram_id):
                    kicked.append(u)
                await asyncio.sleep(1)
            except Exception as e:
                continue

    if kicked:
        logger.info(f'кикнул {kicked}')
        await send_notification(
            tg_bot,
            'Из групп 1 lvl кикнуты:\n' + '\n'.join([f'{u.telegram_username} ({u.telegram_id})' for u in kicked]),
        )

    kicked = []
    for u in downgrade + kicking_both:
        for chat_id in group_2_chat_ids:
            try:
                if await kick_user_from_group(chat_id, u.telegram_id):
                    kicked.append(u)
                await asyncio.sleep(1)
            except Exception as e:
                continue
    if kicked:
        logger.info(f'кикнул {kicked}')
        await send_notification(
            tg_bot,
            'Из групп 2 lvl кикнуты:\n' + '\n'.join([f'{u.telegram_username} ({u.telegram_id})' for u in kicked]),
        )

    return True


@celery_app.task(autostart=False)
def notify_about_subscription_expiration():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_notify_about_subscription_expiration())


@celery_app.task(autostart=False)
def kick_users_with_exp_sub():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_kick_users_with_exp_sub())
