from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import admins
from bot.keyboards import get_main_keyboard
from database.services import create_subscription_plan, get_plans


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
    await message.reply(f'План {new_plan.id} добавлен:\n'
                        f'{new_plan.subscription_time} дней за {new_plan.price}$', reply_markup=get_main_keyboard())
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
