import datetime
import logging

import aiohttp

from bot.consts import STABLES_CONTRACTS, SCANS_API_ADDYS
from bot.config import PAYMENT_WALLET, SCANS_API_KEYS, notification_chat_id
from database.services import get_transaction_hash, get_plan_price_by_id


async def check_payment_valid(plan_id, chain, token, txn_hash) -> bool:
    if not all([plan_id, chain, token, txn_hash]):
        return False

    if await get_transaction_hash(txn_hash):
        return False

    txns = await get_transfers_txns_from_scan(chain, token)
    if not txns:
        return False

    decimals = 10 ** 6  # decimals for stables
    subscription_price = await get_plan_price_by_id(plan_id) * decimals

    for txn in txns:
        if txn.get('hash').lower() == txn_hash.lower():
            if any([
                txn.get('to').lower() != PAYMENT_WALLET.lower(),
                int(txn.get('value')) < subscription_price,
                int(txn.get('timeStamp')) < int(datetime.datetime.now().timestamp()) - 60 * 60
            ]):
                return False
            return True

    return False


async def get_transfers_txns_from_scan(chain, token):
    params = {
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': STABLES_CONTRACTS.get(token.lower()).get(chain.lower()),
        'address': PAYMENT_WALLET,
        'page': '1',
        'offset': '100',
        'startblock': '0',
        'endblock': '999999999',
        'sort': 'desc',
        'apikey': SCANS_API_KEYS.get(chain),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SCANS_API_ADDYS.get(chain), params=params) as resp:
            resp_json = await resp.json()
            return resp_json.get('result')


async def send_notification(bot, msg: str):
    try:
        await bot.send_message(
            notification_chat_id,
            msg,
            parse_mode='Markdown',
        )
    except Exception as e:
        logging.error(e)
