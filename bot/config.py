import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

# group_chat_ids = [-1002106488497]
# admins = [310832640, 493326995, 282984306]

PAYMENT_WALLET = os.getenv('PAYMENT_WALLET')

group_chat_ids = [int(val) for val in os.getenv('group_chat_ids').split(',')]
notifications_chat_id = os.getenv('notifications_chat_id')  # 310832640
admins = [int(val) for val in os.getenv('admins').split(',')]

SCANS_API_KEYS = {
    'polygon': os.getenv('POLYGONSCAN_API_KEY'),
    'optimism': os.getenv('OPTIMISTIC_API_KEY'),
    'arbitrum': os.getenv('ARBISCAN_API_KEY'),
}
