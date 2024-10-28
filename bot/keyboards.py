from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="Подписка"),
        ],
        [
            KeyboardButton(text="Информация"),
        ],
        [
            KeyboardButton(text="Связь с создателем"),
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню"
    )


def get_subscribe_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="Купить подписку"),
        ],
        [
            KeyboardButton(text="Проверить статус подписки"),
        ],
        [
            KeyboardButton(text="Меню"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню"
    )


def get_subscribe_plans_keyboard(active_plans) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text=f"{plan.subscription_time} дней за {plan.price}$", callback_data=f"subscription_{plan.id}"),
        ]
        for plan in active_plans
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_subscribe_chain_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Optimism USDC", callback_data="chain_optimism_usdc"),
            InlineKeyboardButton(text="Optimism USDT", callback_data="chain_optimism_usdt"),
        ],
        [
            InlineKeyboardButton(text="Polygon USDC", callback_data="chain_polygon_usdc"),
            InlineKeyboardButton(text="Polygon USDT", callback_data="chain_polygon_usdt"),
        ],
        [
            InlineKeyboardButton(text="Arbitrum USDC", callback_data="chain_arbitrum_usdc"),
            InlineKeyboardButton(text="Arbitrum USDT", callback_data="chain_arbitrum_usdt"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_info_keyboard(page_number: int, title: str) -> InlineKeyboardMarkup:
    kb = [[]]

    if page_number > 1:
        kb[0].append(InlineKeyboardButton(text="<", callback_data=f"page_{page_number - 1}"))

    if page_number == 1:
        kb[0].append(InlineKeyboardButton(text="<", callback_data=f"page_{page_number}"))

    kb[0].append(InlineKeyboardButton(text=f"{title}", callback_data=f"page_{page_number}"),)

    if page_number < 8:
        kb[0].append(InlineKeyboardButton(text=">", callback_data=f"page_{page_number + 1}"))

    if page_number == 8:
        kb[0].append(InlineKeyboardButton(text=">", callback_data=f"page_{page_number}"))

    return InlineKeyboardMarkup(inline_keyboard=kb)

