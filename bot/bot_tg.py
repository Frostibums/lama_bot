from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode

from bot.handlers import start_router, subscription_router, admin_router, unknown_router
from bot.config import TOKEN
from bot.handlers.get_users_info import users_router

tg_bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

admin_router.message.filter(F.chat.type == "private")
start_router.message.filter(F.chat.type == "private")
subscription_router.message.filter(F.chat.type == "private")
unknown_router.message.filter(F.chat.type == "private")


async def main() -> None:
    dp.include_routers(users_router, admin_router, start_router, subscription_router, unknown_router)
    await dp.start_polling(tg_bot)
