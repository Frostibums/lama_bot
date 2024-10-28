import logging
import os

import loguru
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods import DeleteMessage
from aiogram.types import Message, InputFile, FSInputFile

from bot.keyboards import get_main_keyboard, get_subscribe_keyboard, get_info_keyboard
from bot.texts import TextService

start_router = Router()
section = 'start'


@start_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(TextService.get_text(section, 'greeting'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.voice)
async def voice(message: Message, state: FSMContext) -> None:
    logging.info('\n\n')
    logging.info(f'{message.voice.file_id}')
    await message.bot.send_voice(message.chat.id, message.voice.file_id)

    file = FSInputFile('bot/voices/audio_2024-03-13_19-20-18.ogg')
    await message.bot.send_voice(message.chat.id, file)



@start_router.message(F.text.lower() == "подписка")
async def subscribe(message: Message, state: FSMContext) -> None:
    await state.update_data(plan_id=None, chain=None, txn_hash=None)
    await message.answer(TextService.get_text(section, 'subscription'),
                         reply_markup=get_subscribe_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "информация")
async def group_info(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get('info_msg_id'):
        try:
            await message.bot(DeleteMessage(chat_id=message.chat.id, message_id=int(data.get('info_msg_id'))))
        except Exception as e:
            pass
    answer = await message.answer(TextService.get_text('info', 'page_1'),
                                  reply_markup=get_info_keyboard(1, '1 / 8'),
                                  parse_mode='Markdown')
    await state.update_data(page=1, info_msg_id=answer.message_id, plan_id=None, chain=None, txn_hash=None)


@start_router.message(F.text.lower() == "связь с создателем")
async def contact_creator(message: Message) -> None:
    await message.answer(TextService.get_text(section, 'contacts'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "меню")
async def menu(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    msg_id = data.get('info_msg_id')
    await state.clear()
    await state.update_data(info_msg_id=msg_id)

    await message.answer(TextService.get_text(section, 'menu'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')
