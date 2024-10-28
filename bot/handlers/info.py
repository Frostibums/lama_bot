from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.keyboards import get_info_keyboard
from bot.texts import TextService

info_router = Router()
section = 'info'


@info_router.callback_query(F.data.contains('page_'))
async def get_page(callback: CallbackQuery) -> None:
    page_number = callback.data.split('_')[1]
    try:
        await callback.message.edit_text(TextService.get_text(section, f'page_{page_number}'),
                                         reply_markup=get_info_keyboard(int(page_number), f'{page_number} / 3'),
                                         parse_mode='Markdown')
    except TelegramBadRequest:
        pass
