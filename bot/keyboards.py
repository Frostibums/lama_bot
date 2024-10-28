from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="нет я хочу к ламычу в привку"),
        ],
        [
            KeyboardButton(text="инфа"),
        ],
        [
            KeyboardButton(text="контакты"),
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="выбери пункт меню"
    )


def get_subscribe_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="я псих и хочу стать топ-криптаном"),
        ],
        [
            KeyboardButton(text="ламыч шо по подписке там"),
        ],
        [
            KeyboardButton(text="меню"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="выбери пункт меню"
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
            InlineKeyboardButton(text="Optimism USDT", callback_data="chain_optimism_usdt"),
            InlineKeyboardButton(text="Optimism USDC", callback_data="chain_optimism_usdc"),
            InlineKeyboardButton(text="Optimism USDC.e", callback_data="chain_optimism_usdce"),
        ],
        [
            InlineKeyboardButton(text="Polygon USDT", callback_data="chain_polygon_usdt"),
            InlineKeyboardButton(text="Polygon USDC", callback_data="chain_polygon_usdc"),
            InlineKeyboardButton(text="Polygon USDC.e", callback_data="chain_polygon_usdce"),
        ],
        [
            InlineKeyboardButton(text="Arbitrum USDT", callback_data="chain_arbitrum_usdt"),
            InlineKeyboardButton(text="Arbitrum USDC", callback_data="chain_arbitrum_usdc"),
            InlineKeyboardButton(text="Arbitrum USDC.e", callback_data="chain_arbitrum_usdce"),
        ],
        [
            InlineKeyboardButton(text="Base USDT", callback_data="chain_base_usdt"),
            InlineKeyboardButton(text="Base USDC", callback_data="chain_base_usdc"),
            InlineKeyboardButton(text="Base USDbC", callback_data="chain_base_usdbc"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


