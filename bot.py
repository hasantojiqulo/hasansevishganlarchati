#!/usr/bin/env python3
"""
Sevishganlar Chat Boti
Professional versiya
"""

import logging
import asyncio
import signal
import sys
from datetime import datetime

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import Config
from database import db
import handlers

# Log sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SevishganlarBot:
    def __init__(self):
        self.application = None
        self.is_running = False
        
    async def start(self):
        """Botni ishga tushiradi"""
        try:
            # Botni yaratish
            self.application = Application.builder().token(Config.BOT_TOKEN).build()
            
            # ========== HANDLERLARNI QO'SHISH ==========
            
            # Command handlerlar
            self.application.add_handler(CommandHandler("start", handlers.start_command))
            self.application.add_handler(CommandHandler("help", handlers.help_command))
            self.application.add_handler(CommandHandler("end", handlers.end_command))
            
            # Admin commandlar
            self.application.add_handler(CommandHandler("stat", handlers.admin_stat))
            self.application.add_handler(CommandHandler("users", handlers.admin_users))
            self.application.add_handler(CommandHandler("chats", handlers.admin_chats))
            self.application.add_handler(CommandHandler("broadcast", handlers.admin_broadcast))
            self.application.add_handler(CommandHandler("cleanup", handlers.admin_cleanup))
            
            # Callback query handler
            self.application.add_handler(CallbackQueryHandler(handlers.handle_callback_query))
            
            # Message handler
            self.application.add_handler(MessageHandler(
                filters.ALL & ~filters.COMMAND,
                handlers.handle_message
            ))
            
            # ========== BOTNI ISHGA TUSHIRISH ==========
            
            self.is_running = True
            
            # Start xabari
            logger.info("=" * 50)
            logger.info("🤖 SEVISHGANLAR CHAT BOTI ISHGA TUSHDI")
            logger.info("=" * 50)
            
            try:
                bot_info = await self.application.bot.get_me()
                logger.info(f"📍 Bot username: @{bot_info.username}")
                logger.info(f"🆔 Bot ID: {bot_info.id}")
            except:
                logger.warning("⚠️ Bot ma'lumotlarini olishda xatolik")
            
            logger.info(f"📊 Database: {Config.DATABASE}")
            logger.info(f"👑 Adminlar: {Config.ADMINS}")
            logger.info(f"⏰ Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)
            logger.info("⏹️  To'xtatish uchun Ctrl+C")
            logger.info("=" * 50)
            
            # Signal handlerlar
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Botni ishga tushirish
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Asosiy loop
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot to'xtatildi (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}", exc_info=True)
        finally:
            await self.stop()
    
    def signal_handler(self, signum, frame):
        """Signal handler"""
        logger.info(f"📶 Signal qabul qilindi: {signum}")
        self.is_running = False
    
    async def stop(self):
        """Botni to'xtatadi"""
        try:
            if self.application:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            # Databaseni yopish
            db.close()
            
            logger.info("✅ Bot to'liq to'xtatildi")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Botni to'xtatishda xato: {e}")

def main():
    """Asosiy funksiya"""
    bot = SevishganlarBot()
    
    # Event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot.start())
    finally:
        loop.close()
        sys.exit(0)

if __name__ == '__main__':
    main()
