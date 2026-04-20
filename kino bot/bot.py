import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers.user import user_router
from handlers.admin import admin_router
from middlewares.check_sub import CheckSubscriptionMiddleware

async def main() -> None:
    # Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Middleware'ni ulash
    user_router.message.middleware(CheckSubscriptionMiddleware())
    user_router.callback_query.middleware(CheckSubscriptionMiddleware())
    
    # Routerlarni ulash
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Botni ishga tushirish
    try:
        await dp.start_polling(bot)
    finally:
        from database import close_db
        await close_db()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
