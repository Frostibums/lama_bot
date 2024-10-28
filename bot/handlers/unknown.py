from aiogram import Router
from aiogram.types import Message

from bot.keyboards import get_main_keyboard


unknown_router = Router()


@unknown_router.message()
async def unknown_command(message: Message):
    unknown_msg = 'Не понимаю о чем вы'
    await message.reply(text=unknown_msg, reply_markup=get_main_keyboard())
