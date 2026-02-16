import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import config
from database import init_db, get_db
from handlers import (
    start, cards, info, admin, common
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global error handler
async def global_error_handler(update, exception):
    """Handle errors globally"""
    logger.error(f"Global error: {exception}", exc_info=True)
    try:
        if update.message:
            await update.message.answer(
                "❌ <b>Something went wrong</b>\n\n"
                "Please try again later.",
                parse_mode="HTML"
            )
        elif update.callback_query:
            await update.callback_query.message.answer(
                "❌ <b>Something went wrong</b>\n\n"
                "Please try again later.",
                parse_mode="HTML"
            )
    except:
        pass

async def set_bot_commands(bot: Bot):
    """Set bot commands"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    """Main function"""
    logger.info("Starting bot...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Create bot instance
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register error handler
    dp.errors.register(global_error_handler)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(cards.router)
    dp.include_router(info.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)  # Common should be last
    
    # Inject session dependency
    dp.update.outer_middleware(get_db)
    
    # Set bot commands
    await set_bot_commands(bot)
    
    logger.info("Bot started successfully")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        # Cleanup
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
