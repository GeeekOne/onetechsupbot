import asyncio
import logging
import betterlogging as bl

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.middleware import FSMContextMiddleware

from config import load_config
from handlers.user_private import user_private
from handlers.group import group_router


async def main():
    bl.basic_colorized_config(level=logging.INFO)

    config = load_config('.env')
    bot = Bot(token=config.tg_bot.token)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(
        FSMContextMiddleware(storage=storage, events_isolation=SimpleEventIsolation())
        )

    dp.workflow_data.update({
        'bot': bot,
        'dev_chat_id': config.tg_bot.dev_chat_id,
        'dp': dp
        })
    bot.workflow_data = dp.workflow_data

    dp.include_router(user_private)
    dp.include_router(group_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
