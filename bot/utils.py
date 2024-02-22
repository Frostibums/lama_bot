import aiohttp

from bot.consts import STABLES_CONTRACTS, SCANS_API_ADDYS
from bot.config import PAYMENT_WALLET
from database.services import get_transaction_hash, get_plan_price_by_id


async def check_payment_valid(plan_id, chain, txn_hash) -> bool:
    if not all([plan_id, chain, txn_hash]):
        return False

    if await get_transaction_hash(txn_hash):
        return False

    txn = await get_tron_txn_info(txn_hash)
    if not txn:
        return False

    token_addy = STABLES_CONTRACTS.get('tron')
    decimals = 10 ** 6  # decimals for stables

    if txn.get('contractRet') != 'SUCCESS' or not txn.get('confirmed'):
        return False

    if not txn.get('contract_map') or not txn['contract_map'].get(token_addy):
        return False

    subscription_price = await get_plan_price_by_id(plan_id)
    subscription_price *= decimals
    for info in txn.get('trc20TransferInfo'):
        if all([
            info.get('contract_address') == token_addy,
            info.get('type') == 'Transfer',
            info.get('to_address') == str(PAYMENT_WALLET),
            int(info.get('amount_str', -1)) >= subscription_price,
        ]):
            return True

    return False


async def get_tron_txn_info(txn_hash: str) -> dict:
    params = {
        'hash': txn_hash,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(SCANS_API_ADDYS.get('tron'), params=params) as resp:
            return await resp.json()
