import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

group_chat_ids = [-1002106488497]
notifications_chat_id = 310832640
admins = [310832640, 493326995, 282984306]

SCANS_API_KEYS = {
    'bsc': os.getenv('BSCSCAN_API_KEY'),
    'polygon': os.getenv('POLYGONSCAN_API_KEY'),
    'optimism': os.getenv('OPTIMISTIC_API_KEY'),
    'arbitrum': os.getenv('ARBISCAN_API_KEY'),
}

PAYMENT_WALLET = os.getenv('PAYMENT_WALLET')
