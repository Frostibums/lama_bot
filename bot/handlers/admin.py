import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import admins
from bot.keyboards import get_main_keyboard
from database.services import create_subscription_plan, get_plans, update_plan_activity, change_sub, get_sub_users_info

admin_router = Router()


@admin_router.message(Command("add_plan"))
async def add_plan(message: Message):
    if message.from_user.id not in admins:
        return

    data = message.text.split()
    try:
        days, price = int(data[1]), int(data[2])
    except Exception:
        await message.reply('Ошибка формата вводимых данных')
        return

    new_plan = await create_subscription_plan(days, price)
    await message.reply(
        f'План {new_plan.id} добавлен:\n'
        f'{new_plan.subscription_time} дней за {new_plan.price}$', reply_markup=get_main_keyboard()
    )
    return


@admin_router.message(Command("plans_list"))
async def plans_list(message: Message):
    if message.from_user.id not in admins:
        return

    plans = await get_plans()
    resp = 'Планы в бд:\n'
    for plan in plans:
        resp += f'id: {plan.id:3} | дней: {plan.subscription_time:5} | цена: {plan.price:>4}$ | активен: {plan.is_active}\n'

    await message.reply(resp.strip(), reply_markup=get_main_keyboard())
    return


@admin_router.message(Command("off_plan"))
async def off_plan(message: Message):
    if await _change_plan(message, False):
        await message.reply('План деактивирован', reply_markup=get_main_keyboard())
    return


@admin_router.message(Command("on_plan"))
async def on_plan(message: Message):
    if await _change_plan(message, True):
        await message.reply('План активирован', reply_markup=get_main_keyboard())
    return


async def _change_plan(message: Message, active: bool):
    if message.from_user.id not in admins:
        return False

    data = message.text.split()

    try:
        plan_id = int(data[1])
    except Exception:
        await message.reply('Ошибка формата вводимых данных')
        return False
    await update_plan_activity(plan_id, active=active)

    return True


@admin_router.message(Command("change_sub"))
async def change_subscription(message: Message):
    if message.from_user.id not in admins:
        return False

    data = message.text.split()

    try:
        tg_id, tg_username, end_date = int(data[1]), str(data[2]), str(data[3])
        end_date = datetime.date.fromisoformat(end_date)
    except Exception as e:
        await message.reply(f'Ошибка формата вводимых данных: {e}')
        return False

    if await change_sub(tg_id, tg_username, end_date):
        await message.reply(f'Выдал доступ {tg_username} до {end_date}')
        return True
    await message.reply('Что-то пошло не так')


@admin_router.message(Command("info"))
async def users_info(message: Message):
    if message.from_user.id not in admins:
        return False
    msg = []
    infos = await get_sub_users_info()
    for info in infos:
        print(info)
        msg.append(f'')  # TODO: дописать
    await message.reply('\n'.join(msg))

