from aiogram import Router, F
from aiogram.types import Message

users_router = Router()


@users_router.message(F.text == "+")
async def get_info(message: Message):
    await message.bot.send_message(310832640, f'{message.from_user.id} {message.from_user.username}')
    return
