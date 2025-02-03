import logging
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.config import DOWNLOADS_DIR, admins
from bot.keyboards import get_files_keyboard, get_main_keyboard
from database.services import has_scripts_sub

scripts_router = Router()
section = 'scripts'

logger = logging.getLogger('Scripts')


@scripts_router.message(F.text.lower() == "скрипты")
async def send_files_keyboard(message: Message):
    """Отправляет клавиатуру с файлами из папки downloads."""
    if message.from_user.id not in admins and not await has_scripts_sub(message.from_user.id):
        await message.answer(
            "Для доступа к скриптам необходимо купить подписку второго уровня",
            reply_markup=await get_main_keyboard(),
        )
        logger.info(
            f'{message.from_user.username} ({message.from_user.id}) пытался получить доступ к скриптам без подписки'
        )
    await message.answer("⏱ После нажатия на кнопку, возможно, придется немного подождать "
                         "- в зависимости от размера файла.\n"
                         "Бот обработает Ваш запрос.\n\n"
                         "Выберите файл:", reply_markup=get_files_keyboard())


@scripts_router.callback_query(F.data.startswith("file_"))
async def send_file(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку файла и отправляет файл пользователю."""
    if callback.message.from_user.id not in admins and not await has_scripts_sub(callback.message.from_user.id):
        await callback.message.answer(
            "Для доступа к скриптам необходимо купить подписку второго уровня",
            reply_markup=await get_main_keyboard(),
        )
        logger.info(
            f'{callback.message.from_user.username} ({callback.message.from_user.id}) '
            f'пытался получить доступ к скриптам без подписки'
        )

    file_name = callback.data[len("file_"):]
    file_path = os.path.join(DOWNLOADS_DIR, file_name)

    if os.path.exists(file_path):
        input_file = FSInputFile(file_path)
        await callback.message.answer_document(document=input_file)
    else:
        await callback.message.answer("Файл не найден 😢")

    await callback.answer()
