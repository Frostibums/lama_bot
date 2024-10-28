import asyncio
import logging

from bot.bot_tg import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
