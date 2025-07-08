import logging
import asyncio
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import Config
from bot_handler import TelegramBotHandler
from health_server import HealthServer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TelegramVoiceBot:
    def __init__(self):
        # Validate configuration
        try:
            Config.validate()
            logger.info("Configuration validated successfully")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize bot handler
        self.bot_handler = TelegramBotHandler()
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Initialize health server
        self.health_server = HealthServer()
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all message and command handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.bot_handler.handle_start))
        self.application.add_handler(CommandHandler("help", self.bot_handler.handle_help))
        
        # Message handler for text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.bot_handler.handle_message)
        )
        
        logger.info("Handlers setup completed")
    
    async def start(self):
        """Start the bot"""
        try:
            # Create temp directory for audio files
            os.makedirs("temp", exist_ok=True)
            
            # Start health server
            self.health_server.run_in_background()
            
            logger.info("Starting Telegram Voice Bot...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot is running! Press Ctrl+C to stop.")
            
            # Keep the bot running
            await self.application.idle()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        
        # Clean up temp files
        try:
            import shutil
            if os.path.exists("temp"):
                shutil.rmtree("temp")
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

async def main():
    """Main application entry point"""
    bot = TelegramVoiceBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1) 