import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Database fayl
    DATABASE = "sevishganlar.db"
    
    # Admin ID lar (yangi qo'shishingiz mumkin)
    ADMINS = [7917659197]  # O'zingizning ID ni kiriting
    
    # Sozlamalar
    MAX_MESSAGE_LENGTH = 4000
    REQUEST_TIMEOUT = 60  # sekund
    CLEANUP_INTERVAL = 3600  # 1 soat
    
    # Xabarlar
    MESSAGES = {
        "welcome": "👋 Salom {name}! Sevishganlar Chat botiga xush kelibsiz!",
        "your_id": "🆔 Sizning ID: `{user_id}`",
        "how_get_id": "📋 ID ni qanday olish mumkin?\n1. @userinfobot ga boring\n2. /start bosing\n3. ID raqamingizni oling",
        "partner_add": "💑 Sevgan odamingizning ID sini kiriting:",
        "invalid_id": "❌ ID faqat raqamlardan iborat bo'lishi kerak!",
        "self_id": "❌ O'zingizning ID ingizni kiritdingiz!",
        "user_busy": "❌ Bu foydalanuvchi allaqachon boshqa chatda!",
        "invite_sent": "✅ Taklif yuborildi!\n👤 Kimga: {name}\n🆔 ID: `{id}`",
        "invite_received": "💌 *Yangi chat taklifi!*\n\n{name} sizni chatga taklif qilmoqda!",
        "chat_started": "✅ Chat ochildi! 💑\nEndi bir-biringizga xabar yuborishingiz mumkin.",
        "chat_ended": "🔚 Chat tugatildi",
        "no_active_chat": "Sizda faol chat yo'q",
        "message_sent": "✅ Xabar yuborildi",
        "message_not_sent": "❌ Xabar yuborilmadi",
        "help_text": """
🤖 *Sevishganlar Chat Boti - Yordam*

*Qanday ishlaydi?*
1. /start - Botni ishga tushirish
2. "Sevgan odamimni qo'shish" tugmasini bosing
3. Sherigingizning ID sini kiriting
4. Sherigingiz taklifni qabul qilsa, chat ochiladi

*ID ni qanday olaman?*
• @userinfobot ga boring va /start bosing
• Sizga ID raqamingiz ko'rsatiladi

*Muhim eslatmalar:*
• Faqat 2 kishi chat qilishi mumkin
• Chatni istalgan vaqt /end bilan tugatishingiz mumkin
• Barcha xabarlar maxfiy saqlanadi
""",
        "admin_help": """
👑 *Admin Paneli*

/stat - Bot statistikasi
/users - Barcha foydalanuvchilar
/chats - Faol chatlar
/broadcast - Xabar yuborish
/cleanup - Eski ma'lumotlarni tozalash
"""
    }
