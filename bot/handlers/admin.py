import datetime
import logging
import os

import aiofiles
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from tabulate import tabulate

from bot.config import admins, TOKEN, DOWNLOADS_DIR
from bot.keyboards import get_main_keyboard, delete_files_keyboard
from database.services import create_subscription_plan, get_plans, update_plan_activity, give_sub, get_sub_users_info

admin_router = Router()


logger = logging.getLogger('Admin')


@admin_router.message(Command('help'))
async def get_help(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/help`')
    if message.from_user.id not in admins:
        return

    admin_commands = {
        '/help': 'Показать список доступных команд',
        '/info': 'Показать информацию о пользователях',
        '/add_plan': 'Добавить план.\n'
                     'Вводимые параметры: Количество дней, Цена в $, Уровень (1 / 2), Текст для кнопки.\n'
                     'Пример:\n`/add_plan 30 90 1 Подписка 1 уровня на 30 дней за 90$`',
        '/plans': 'Вывести имеющиеся в БД планы.',
        '/plan_off': 'Деактивировать план по ID из БД.\nПример: `/plan_off 2`',
        '/plan_on': 'Активировать план по ID из БД.\nПример: `/plan_on 2`',
        '/give_sub': 'Выдать подписку пользователю.\n'
                     'Вводимые параметры: Телеграм ID, Телеграм юзернейм, '
                     'Дата окончания подписки (в формате ISO), Доступ к скриптам (да/нет)\n'
                     'Пример:\n`/give_sub 310832640 MrOatmeal 2025-10-05 Да`',
        '/delete': 'Удалить скрипт(ы).\n',
    }

    help_text = '**Доступные админские команды:**\n\n'
    help_text += '\n\n'.join(f'**`{cmd}`** — {desc}' for cmd, desc in admin_commands.items())
    help_text += ('\nДля добавления новых скриптов достаточно отправить боту **.zip** или **.rar** архив.\n'
                  'Файл должен иметь название не более 45 символов.')
    await message.answer(help_text, parse_mode='Markdown')


@admin_router.message(Command('add_plan'))
async def add_plan(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/add_plan`')

    if message.from_user.id not in admins:
        return

    data = message.text.split()
    try:
        days, price, level, text = int(data[1]), int(data[2]), int(data[3]), str(' '.join(data[4:]))
    except Exception:
        await message.reply('Ошибка формата вводимых данных')
        return

    new_plan = await create_subscription_plan(days, price, level, text)
    await message.reply(
        f'План {new_plan.id} добавлен:\n'
        f'{new_plan.subscription_time} дней за {new_plan.price}$',
        reply_markup= await get_main_keyboard(telegram_id=message.from_user.id),
    )
    return


@admin_router.message(Command('plans'))
async def plans_list(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/plans`')

    if message.from_user.id not in admins:
        return

    plans = await get_plans()
    await message.reply('Планы в бд:\n\n', reply_markup= await get_main_keyboard(telegram_id=message.from_user.id))
    for i, plan in enumerate(plans):
        plan_info = (f'id: {plan.id}\n'
                     f'Кол-во дней: {plan.subscription_time}\n'
                     f'Цена: {plan.price}$\n'
                     f'v: {plan.level}\n'
                     f'Текст: {plan.text}\n'
                     f'Активен: {plan.is_active}\n'
                     f'\n')
        await message.answer(plan_info)

    return


@admin_router.message(Command('plan_off'))
async def off_plan(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/plan_off`')

    if await _change_plan(message, False):
        await message.reply('План деактивирован', reply_markup= await get_main_keyboard(telegram_id=message.from_user.id))
    return


@admin_router.message(Command('plan_on'))
async def on_plan(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/plan_on`')

    if await _change_plan(message, True):
        await message.reply('План активирован', reply_markup= await get_main_keyboard(telegram_id=message.from_user.id))
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


@admin_router.message(Command('give_sub'))
async def give_subscription(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/give_sub`')

    if message.from_user.id not in admins:
        return False

    data = message.text.split()

    try:
        tg_id, tg_username, end_date, scripts = int(data[1]), str(data[2]).strip('@'), str(data[3]), str(data[4])
        end_date = datetime.date.fromisoformat(end_date)
    except Exception as e:
        await message.reply(f'Ошибка формата вводимых данных: {e}')
        return False

    scripts_allowance = True if scripts.strip().lower() == 'да' else False
    if await give_sub(tg_id, tg_username, end_date, scripts_allowance):
        await message.reply(f'Выдал доступ {tg_username} до {end_date}')
        return True
    await message.reply('Что-то пошло не так')


@admin_router.message(Command('info'))
async def users_info(message: Message):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/info`')

    if message.from_user.id not in admins:
        return False
    infos = await get_sub_users_info()

    table_data = [
        [
            i + 1,
            user.telegram_username,
            str(user.telegram_id),
            user.registered_at.strftime('%Y-%m-%d'),
            user.end_time.strftime('%Y-%m-%d') if user.end_time else '—',
            user.scripts_end_time.strftime('%Y-%m-%d') if user.scripts_end_time else '—',
        ]
        for i, user in enumerate(infos)
    ]

    table_str = tabulate(
        table_data,
        headers=['#', 'Username', 'Telegram ID', 'Registered', 'Sub End', 'Scripts End'],
        tablefmt='github'
    )

    max_length = 4096
    parts = [table_str[i:i + max_length] for i in range(0, len(table_str), max_length)]

    for part in parts:
        await message.answer(f'<pre>{part}</pre>', parse_mode='HTML')


@admin_router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    logger.info(f'{message.from_user.username} ({message.from_user.id}) пытается загрузить файл...')

    if message.from_user.id not in admins:
        logger.info(f'{message.from_user.username} ({message.from_user.id}) Только админы могут загружать файлы')
        await message.answer(f'Только админы могут загружать файлы')
        return

    file_id = message.document.file_id
    file_name = message.document.file_name.strip()
    if not (file_name.endswith('.zip') or file_name.endswith('.rar')):
        msg = f'{file_name} - Неверный формат файла, принимаем только <b>zip</b> и <b>rar</b>'
        logger.error(msg)
        await message.answer(msg)
        return
    if len(file_name) > 45:
        msg = f'{file_name} - Название файла должно содержать не более <b>45</b> символов'
        logger.error(msg)
        await message.answer(msg)
        return

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    file_content = await bot.download_file(file_path)

    save_dir = f'./{DOWNLOADS_DIR}'
    os.makedirs(save_dir, exist_ok=True)
    save_path = f'./{DOWNLOADS_DIR}/{file_name}'
    async with aiofiles.open(save_path, 'wb') as f:
        await f.write(file_content.read())

    logger.info(f'{message.from_user.username} ({message.from_user.id}) згрузил скрипт {file_name}')
    await message.answer(f'Файл <b>{file_name}</b> сохранен ✅')


@admin_router.message(Command('delete'))
async def delete_files(message: Message):
    """Отправляет клавиатуру с файлами из папки scripts."""
    logger.info(f'{message.from_user.username} ({message.from_user.id}) воспользовался командой `/delete`')

    if message.from_user.id not in admins:
        await message.answer(f'Только админы могут удалять файлы')
        return
    await message.answer('🗑 Выберите файл:', reply_markup=delete_files_keyboard())


@admin_router.callback_query(F.data.startswith('del_file_'))
async def delete_file_callback(callback: CallbackQuery):
    """Удаляет выбранный файл."""
    if callback.from_user.id not in admins:
        await callback.message.answer(f'Только админы могут удалять файлы')
        return

    file_name = callback.data[len('del_file_'):]
    file_path = os.path.join(DOWNLOADS_DIR, file_name)

    if os.path.exists(file_path):
        os.remove(file_path)
        await callback.message.answer(f'✅ Файл `{file_name}` удалён.')
        logger.info(
            f'{callback.message.from_user.username} ({callback.message.from_user.id}) удалил файл {file_name}'
        )
    else:
        await callback.message.answer('⚠ Файл не найден.')

    await callback.answer()
