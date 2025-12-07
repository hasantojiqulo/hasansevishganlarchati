import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import db

logger = logging.getLogger(__name__)

# ========== COMMAND HANDLERS ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    try:
        user = update.effective_user
        user_id = user.id
        
        # Foydalanuvchini database ga qo'shamiz
        db.add_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Klaviatura
        keyboard = [
            [InlineKeyboardButton("💑 Sevgan odamimni qo'shish", callback_data='add_partner')],
            [InlineKeyboardButton("❌ Chatni tugatish", callback_data='end_chat')],
            [InlineKeyboardButton("ℹ️ Yordam", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Xabar
        message = (
            f"{Config.MESSAGES['welcome'].format(name=user.first_name)}\n\n"
            f"{Config.MESSAGES['your_id'].format(user_id=user_id)}\n\n"
            f"{Config.MESSAGES['how_get_id']}"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Foydalanuvchi {user_id} start bosdi")
        
    except Exception as e:
        logger.error(f"Start command xatosi: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help komandasi"""
    await update.message.reply_text(
        Config.MESSAGES['help_text'],
        parse_mode='Markdown'
    )

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/end komandasi - chatni tugatish"""
    try:
        user_id = update.effective_user.id
        
        # Faol chatni topamiz
        chat = db.get_active_chat(user_id)
        
        if not chat:
            await update.message.reply_text(Config.MESSAGES['no_active_chat'])
            return
        
        # Chatni tugatamiz
        if db.end_chat(chat['chat_id']):
            # Sherigga xabar
            partner_id = chat['user2_id'] if chat['user1_id'] == user_id else chat['user1_id']
            
            try:
                await context.bot.send_message(
                    chat_id=partner_id,
                    text="🔚 *Chat tugatildi*\n\nSherigingiz chatni tugatdi.",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            await update.message.reply_text(
                Config.MESSAGES['chat_ended'],
                parse_mode='Markdown'
            )
            
            logger.info(f"Chat tugatildi: {chat['chat_id']}")
        else:
            await update.message.reply_text("❌ Chatni tugatishda xatolik")
            
    except Exception as e:
        logger.error(f"End command xatosi: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")

# ========== CALLBACK QUERY HANDLERS ==========

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha callback querylar"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == 'add_partner':
        await add_partner_callback(query, context)
    elif data == 'end_chat':
        await end_chat_callback(query, context)
    elif data == 'help':
        await help_callback(query, context)
    elif data.startswith('accept_'):
        await accept_invitation(query, context)
    elif data.startswith('reject_'):
        await reject_invitation(query, context)

async def add_partner_callback(query, context):
    """Partner qo'shish"""
    user_id = query.from_user.id
    
    # Faol chatni tekshiramiz
    if db.get_active_chat(user_id):
        await query.edit_message_text("⚠️ Siz allaqachon faol chatdasiz!")
        return
    
    await query.edit_message_text(
        Config.MESSAGES['partner_add'],
        parse_mode='Markdown'
    )
    
    # Holatni saqlaymiz
    context.user_data['waiting_for_partner_id'] = True

async def end_chat_callback(query, context):
    """Chatni tugatish (callback)"""
    user_id = query.from_user.id
    
    chat = db.get_active_chat(user_id)
    if not chat:
        await query.edit_message_text(Config.MESSAGES['no_active_chat'])
        return
    
    if db.end_chat(chat['chat_id']):
        # Sherigga xabar
        partner_id = chat['user2_id'] if chat['user1_id'] == user_id else chat['user1_id']
        
        try:
            await context.bot.send_message(
                partner_id,
                "🔚 *Chat tugatildi*\n\nSherigingiz chatni tugatdi.",
                parse_mode='Markdown'
            )
        except:
            pass
        
        await query.edit_message_text(
            Config.MESSAGES['chat_ended'],
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ Chatni tugatishda xatolik")

async def help_callback(query, context):
    """Yordam (callback)"""
    await query.edit_message_text(
        Config.MESSAGES['help_text'],
        parse_mode='Markdown'
    )

# ========== INVITATION HANDLERS ==========

async def accept_invitation(query, context):
    """Taklifni qabul qilish"""
    try:
        receiver_id = query.from_user.id
        data = query.data.split('_')
        
        if len(data) < 2:
            await query.edit_message_text("❌ Xatolik!")
            return
        
        sender_id = int(data[1])
        
        # Taklifni tekshiramiz
        invitation = db.get_invitation(sender_id, receiver_id)
        if not invitation:
            await query.edit_message_text("❌ Taklif topilmadi!")
            return
        
        # Taklif holatini yangilaymiz
        db.update_invitation_status(sender_id, receiver_id, 'accepted')
        
        # Chat yaratamiz
        chat_id = db.create_chat(sender_id, receiver_id)
        
        if chat_id:
            # Qabul qiluvchiga xabar
            await query.edit_message_text(
                Config.MESSAGES['chat_started'],
                parse_mode='Markdown'
            )
            
            # Taklif yuboruvchiga xabar
            sender_name = query.from_user.first_name
            try:
                await context.bot.send_message(
                    chat_id=sender_id,
                    text=f"🎉 *{sender_name} chatni qabul qildi!*\n\n"
                         f"{Config.MESSAGES['chat_started']}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Taklif yuboruvchiga xabar yuborishda xato: {e}")
            
            logger.info(f"Yangi chat yaratildi: {chat_id}")
        else:
            await query.edit_message_text("❌ Chat yaratishda xatolik!")
            
    except Exception as e:
        logger.error(f"Taklifni qabul qilishda xato: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi!")

async def reject_invitation(query, context):
    """Taklifni rad etish"""
    try:
        receiver_id = query.from_user.id
        data = query.data.split('_')
        
        if len(data) < 2:
            return
        
        sender_id = int(data[1])
        
        # Taklif holatini yangilaymiz
        db.update_invitation_status(sender_id, receiver_id, 'rejected')
        
        await query.edit_message_text("❌ Taklif rad etildi.")
        
        # Taklif yuboruvchiga xabar
        try:
            await context.bot.send_message(
                chat_id=sender_id,
                text=f"❌ {query.from_user.first_name} sizning taklifingizni rad etdi."
            )
        except:
            pass
            
    except Exception as e:
        logger.error(f"Taklifni rad etishda xato: {e}")

# ========== MESSAGE HANDLERS ==========

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha xabarlarni qayta ishlash"""
    try:
        user_id = update.effective_user.id
        
        # Faollikni yangilaymiz
        db.update_user_activity(user_id)
        
        # 1. Agar partner ID kutayotgan bo'lsa
        if context.user_data.get('waiting_for_partner_id'):
            await process_partner_id(update, context)
            return
        
        # 2. Agar chat faol bo'lsa
        chat = db.get_active_chat(user_id)
        if chat:
            await forward_message(update, context, chat)
            return
        
        # 3. Boshqa holatda
        await update.message.reply_text(
            "🤖 *Sevishganlar Chat Boti*\n\n"
            "💑 Chat boshlash uchun /start bosing\n"
            "❓ Yordam uchun /help",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Xabarni qayta ishlashda xato: {e}")

async def process_partner_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Partner ID ni qayta ishlash"""
    try:
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # ID ni tekshiramiz
        if not text.isdigit():
            await update.message.reply_text(Config.MESSAGES['invalid_id'])
            return
        
        partner_id = int(text)
        
        # O'zini o'ziga yubormaslik
        if partner_id == user_id:
            await update.message.reply_text(Config.MESSAGES['self_id'])
            return
        
        # Partnerning faol chatda emasligini tekshiramiz
        if db.get_active_chat(partner_id):
            await update.message.reply_text(Config.MESSAGES['user_busy'])
            context.user_data['waiting_for_partner_id'] = False
            return
        
        # Partner mavjudligini tekshiramiz
        try:
            partner_chat = await context.bot.get_chat(partner_id)
            partner_name = partner_chat.first_name
            
            # Test xabari
            test_msg = await context.bot.send_message(partner_id, "🔍 Tekshiruv...")
            await context.bot.delete_message(partner_id, test_msg.message_id)
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ *Xatolik!*\n\n"
                f"*Sabablar:*\n"
                f"1. ID noto'g'ri\n"
                f"2. Foydalanuvchi botni bloklagan\n"
                f"3. Foydalanuvchi botga /start bosmagan\n\n"
                f"Bot: @{(await context.bot.get_me()).username}",
                parse_mode='Markdown'
            )
            context.user_data['waiting_for_partner_id'] = False
            return
        
        # Taklif yaratamiz
        if db.create_invitation(user_id, partner_id):
            # Taklifni yuboramiz
            keyboard = [
                [
                    InlineKeyboardButton("✅ Qabul qilish", callback_data=f'accept_{user_id}'),
                    InlineKeyboardButton("❌ Rad etish", callback_data=f'reject_{user_id}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            sender_name = update.effective_user.first_name
            await context.bot.send_message(
                chat_id=partner_id,
                text=Config.MESSAGES['invite_received'].format(name=sender_name) +
                     f"\n\n👤 *Taklif qiluvchi:* {sender_name}\n"
                     f"🆔 *ID:* `{user_id}`\n\n"
                     f"Chatni qabul qilasizmi?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Tasdiqlash xabari
            await update.message.reply_text(
                Config.MESSAGES['invite_sent'].format(name=partner_name, id=partner_id),
                parse_mode='Markdown'
            )
            
            logger.info(f"Taklif yuborildi: {user_id} -> {partner_id}")
        else:
            await update.message.reply_text("❌ Taklif yuborishda xatolik!")
        
        context.user_data['waiting_for_partner_id'] = False
        
    except Exception as e:
        logger.error(f"Partner ID ni qayta ishlashda xato: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi!")
        context.user_data['waiting_for_partner_id'] = False

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE, chat):
    """Xabarni sherigga yo'naltirish"""
    try:
        user_id = update.effective_user.id
        chat_id = chat['chat_id']
        
        # Sherikni aniqlaymiz
        if chat['user1_id'] == user_id:
            partner_id = chat['user2_id']
        else:
            partner_id = chat['user1_id']
        
        # Xabarni yuboramiz
        message_text = update.message.text or update.message.caption or ""
        sender_name = update.effective_user.first_name
        
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=partner_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📸 *{sender_name}:*\n{message_text}" if message_text else f"📸 *{sender_name}* rasm yubordi",
                parse_mode='Markdown'
            )
            message_type = 'photo'
            content = 'photo'
            
        elif update.message.video:
            await context.bot.send_video(
                chat_id=partner_id,
                video=update.message.video.file_id,
                caption=f"🎥 *{sender_name}:*\n{message_text}" if message_text else f"🎥 *{sender_name}* video yubordi",
                parse_mode='Markdown'
            )
            message_type = 'video'
            content = 'video'
            
        elif update.message.document:
            await context.bot.send_document(
                chat_id=partner_id,
                document=update.message.document.file_id,
                caption=f"📄 *{sender_name}:*\n{message_text}" if message_text else f"📄 *{sender_name}* fayl yubordi",
                parse_mode='Markdown'
            )
            message_type = 'document'
            content = 'document'
            
        elif update.message.audio:
            await context.bot.send_audio(
                chat_id=partner_id,
                audio=update.message.audio.file_id,
                caption=f"🎵 *{sender_name}:*\n{message_text}" if message_text else f"🎵 *{sender_name}* audio yubordi",
                parse_mode='Markdown'
            )
            message_type = 'audio'
            content = 'audio'
            
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=partner_id,
                voice=update.message.voice.file_id,
                caption=f"🎤 *{sender_name}:*\n{message_text}" if message_text else f"🎤 *{sender_name}* ovoz yubordi",
                parse_mode='Markdown'
            )
            message_type = 'voice'
            content = 'voice'
            
        elif update.message.sticker:
            await context.bot.send_sticker(
                chat_id=partner_id,
                sticker=update.message.sticker.file_id
            )
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"🩷 *{sender_name}* sticker yubordi",
                parse_mode='Markdown'
            )
            message_type = 'sticker'
            content = 'sticker'
            
        else:
            await context.bot.send_message(
                chat_id=partner_id,
                text=f"💬 *{sender_name}:*\n{update.message.text}",
                parse_mode='Markdown'
            )
            message_type = 'text'
            content = update.message.text[:100]  # 100 belgigacha
        
        # Xabarni database ga saqlaymiz
        db.add_message(chat_id, user_id, message_type, content)
        
        # Tasdiqlash (iste'faga qarab)
        # await update.message.reply_text(Config.MESSAGES['message_sent'])
        
        logger.info(f"Xabar yuborildi: {user_id} -> {partner_id}")
        
    except Exception as e:
        logger.error(f"Xabarni yo'naltirishda xato: {e}")
        await update.message.reply_text(Config.MESSAGES['message_not_sent'])

# ========== ADMIN HANDLERS ==========

async def admin_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot statistikasi (/stat)"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    stats = db.get_stats()
    
    message = (
        "📊 *Bot Statistikasi*\n\n"
        f"👥 *Jami foydalanuvchilar:* {stats.get('total_users', 0)}\n"
        f"💬 *Faol chatlar:* {stats.get('active_chats', 0)}\n"
        f"📅 *Bugungi faollar:* {stats.get('today_active', 0)}\n"
        f"✉️ *Jami xabarlar:* {stats.get('total_messages', 0)}\n"
        f"🗄️ *Database fayli:* `{Config.DATABASE}`"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha foydalanuvchilar (/users)"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("📭 Hozircha foydalanuvchilar yo'q")
        return
    
    message = "👥 *Barcha foydalanuvchilar:*\n\n"
    for user in users[:50]:  # Faqat 50 tasini ko'rsatamiz
        username = f"@{user['username']}" if user['username'] else "Yo'q"
        message += (
            f"🆔 *ID:* `{user['user_id']}`\n"
            f"👤 *Ism:* {user['first_name']}\n"
            f"📱 *Username:* {username}\n"
            f"⏰ *Oxirgi faollik:* {user['last_active'][:19]}\n"
            f"────────────────────\n"
        )
    
    if len(users) > 50:
        message += f"\n... va yana {len(users) - 50} ta foydalanuvchi"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha chatlar (/chats)"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    chats = db.get_all_chats()
    
    if not chats:
        await update.message.reply_text("📭 Hozircha chatlar yo'q")
        return
    
    message = "💬 *Barcha chatlar:*\n\n"
    for chat in chats[:20]:  # Faqat 20 tasini ko'rsatamiz
        status = "✅ Faol" if chat['is_active'] else "❌ Tugatilgan"
        message += (
            f"🆔 *Chat ID:* `{chat['chat_id']}`\n"
            f"👤 *User 1:* {chat['user1_name']} (`{chat['user1_id']}`)\n"
            f"👤 *User 2:* {chat['user2_name']} (`{chat['user2_id']}`)\n"
            f"📅 *Yaratilgan:* {chat['created_at'][:19]}\n"
            f"📊 *Holat:* {status}\n"
            f"────────────────────\n"
        )
    
    if len(chats) > 20:
        message += f"\n... va yana {len(chats) - 20} ta chat"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabar yuborish (/broadcast)"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 *Broadcast qilish*\n\n"
            "Foydalanish: `/broadcast <xabar>`\n\n"
            "Misol: `/broadcast Yangilik! Bot yangilandi!`",
            parse_mode='Markdown'
        )
        return
    
    message = ' '.join(context.args)
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("📭 Foydalanuvchilar topilmadi")
        return
    
    await update.message.reply_text(
        f"📢 {len(users)} ta foydalanuvchiga xabar yuborilmoqda..."
    )
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 *Botdan xabar:*\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except:
            failed += 1
    
    await update.message.reply_text(
        f"✅ *Broadcast natijasi:*\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}\n"
        f"📊 Jami: {len(users)}",
        parse_mode='Markdown'
    )

async def admin_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eski ma'lumotlarni tozalash (/cleanup)"""
    user_id = update.effective_user.id
    
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    await update.message.reply_text("🧹 Eski ma'lumotlar tozalanmoqda...")
    
    if db.cleanup_old_data():
        await update.message.reply_text("✅ Ma'lumotlar muvaffaqiyatli tozalandi!")
    else:
        await update.message.reply_text("❌ Tozalashda xatolik yuz berdi!")
