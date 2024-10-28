from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import get_main_keyboard, get_subscribe_keyboard
from bot.texts import TextService

start_router = Router()
section = 'start'


@start_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(TextService.get_text(section, 'greeting'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "нет я хочу к ламычу в привку")
async def subscribe(message: Message, state: FSMContext) -> None:
    await state.update_data(plan_id=None, chain=None, txn_hash=None)
    await message.answer(TextService.get_text(section, 'subscription'),
                         reply_markup=get_subscribe_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "инфа")
async def group_info(message: Message) -> None:
    await message.answer(TextService.get_text(section, 'info'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "контакты")
async def contact_creator(message: Message) -> None:
    await message.answer(TextService.get_text(section, 'contacts'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')


@start_router.message(F.text.lower() == "меню")
async def menu(message: Message) -> None:
    await message.answer(TextService.get_text(section, 'menu'),
                         reply_markup=get_main_keyboard(),
                         parse_mode='Markdown')
