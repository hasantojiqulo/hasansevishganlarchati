import sqlite3
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Database ga ulanadi"""
        try:
            self.conn = sqlite3.connect(Config.DATABASE, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info("Database ga ulandi")
        except Exception as e:
            logger.error(f"Database ga ulanishda xato: {e}")
    
    def create_tables(self):
        """Jadvallarni yaratadi"""
        try:
            # Foydalanuvchilar jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Chatlar jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user1_id) REFERENCES users(user_id),
                    FOREIGN KEY (user2_id) REFERENCES users(user_id)
                )
            ''')
            
            # Xabarlar jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    sender_id INTEGER,
                    message_type TEXT,
                    content TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                    FOREIGN KEY (sender_id) REFERENCES users(user_id)
                )
            ''')
            
            # Takliflar jadvali
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS invitations (
                    invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    status TEXT DEFAULT 'pending', -- pending, accepted, rejected
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id),
                    FOREIGN KEY (receiver_id) REFERENCES users(user_id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Jadvallar yaratildi/yangilandi")
            
        except Exception as e:
            logger.error(f"Jadvallarni yaratishda xato: {e}")
    
    # ========== USER OPERATIONS ==========
    
    def add_user(self, user_id, username, first_name, last_name=None):
        """Yangi foydalanuvchi qo'shadi"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Foydalanuvchi qo'shishda xato: {e}")
            return False
    
    def get_user(self, user_id):
        """Foydalanuvchini olish"""
        try:
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Foydalanuvchini olishda xato: {e}")
            return None
    
    def update_user_activity(self, user_id):
        """Foydalanuvchi faolligini yangilaydi"""
        try:
            self.cursor.execute(
                'UPDATE users SET last_active = ? WHERE user_id = ?',
                (datetime.now(), user_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Faollikni yangilashda xato: {e}")
    
    def get_all_users(self):
        """Barcha foydalanuvchilarni olish"""
        try:
            self.cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Barcha foydalanuvchilarni olishda xato: {e}")
            return []
    
    # ========== CHAT OPERATIONS ==========
    
    def create_chat(self, user1_id, user2_id):
        """Yangi chat yaratadi"""
        try:
            self.cursor.execute('''
                INSERT INTO chats (user1_id, user2_id, created_at)
                VALUES (?, ?, ?)
            ''', (user1_id, user2_id, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Chat yaratishda xato: {e}")
            return None
    
    def get_active_chat(self, user_id):
        """Foydalanuvchining faol chatini topadi"""
        try:
            self.cursor.execute('''
                SELECT * FROM chats 
                WHERE (user1_id = ? OR user2_id = ?) 
                AND is_active = 1
                LIMIT 1
            ''', (user_id, user_id))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Faol chatni olishda xato: {e}")
            return None
    
    def get_chat_partner(self, user_id):
        """Chat sherigini topadi"""
        chat = self.get_active_chat(user_id)
        if chat:
            if chat['user1_id'] == user_id:
                return chat['user2_id']
            else:
                return chat['user1_id']
        return None
    
    def end_chat(self, chat_id):
        """Chatni tugatadi"""
        try:
            self.cursor.execute('''
                UPDATE chats 
                SET is_active = 0, ended_at = ?
                WHERE chat_id = ?
            ''', (datetime.now(), chat_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Chatni tugatishda xato: {e}")
            return False
    
    def get_all_chats(self):
        """Barcha chatlarni olish"""
        try:
            self.cursor.execute('''
                SELECT c.*, 
                       u1.first_name as user1_name,
                       u2.first_name as user2_name
                FROM chats c
                LEFT JOIN users u1 ON c.user1_id = u1.user_id
                LEFT JOIN users u2 ON c.user2_id = u2.user_id
                ORDER BY c.created_at DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Barcha chatlarni olishda xato: {e}")
            return []
    
    # ========== INVITATION OPERATIONS ==========
    
    def create_invitation(self, sender_id, receiver_id):
        """Yangi taklif yaratadi"""
        try:
            # Avval mavjud taklifni tekshiramiz
            self.cursor.execute('''
                SELECT * FROM invitations 
                WHERE sender_id = ? AND receiver_id = ? 
                AND status = 'pending'
            ''', (sender_id, receiver_id))
            
            if self.cursor.fetchone():
                return False  # Taklif allaqachon mavjud
            
            self.cursor.execute('''
                INSERT INTO invitations (sender_id, receiver_id)
                VALUES (?, ?)
            ''', (sender_id, receiver_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Taklif yaratishda xato: {e}")
            return False
    
    def get_invitation(self, sender_id, receiver_id):
        """Taklifni olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM invitations 
                WHERE sender_id = ? AND receiver_id = ? 
                AND status = 'pending'
            ''', (sender_id, receiver_id))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Taklifni olishda xato: {e}")
            return None
    
    def update_invitation_status(self, sender_id, receiver_id, status):
        """Taklif holatini yangilaydi"""
        try:
            self.cursor.execute('''
                UPDATE invitations 
                SET status = ?, responded_at = ?
                WHERE sender_id = ? AND receiver_id = ? 
                AND status = 'pending'
            ''', (status, datetime.now(), sender_id, receiver_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Taklif holatini yangilashda xato: {e}")
            return False
    
    # ========== MESSAGE OPERATIONS ==========
    
    def add_message(self, chat_id, sender_id, message_type, content):
        """Xabar qo'shadi"""
        try:
            self.cursor.execute('''
                INSERT INTO messages (chat_id, sender_id, message_type, content)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, sender_id, message_type, content))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Xabar qo'shishda xato: {e}")
            return None
    
    # ========== STATISTICS ==========
    
    def get_stats(self):
        """Bot statistikasini olish"""
        try:
            stats = {}
            
            # Foydalanuvchilar soni
            self.cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = self.cursor.fetchone()[0]
            
            # Faol chatlar soni
            self.cursor.execute('SELECT COUNT(*) FROM chats WHERE is_active = 1')
            stats['active_chats'] = self.cursor.fetchone()[0]
            
            # Bugungi foydalanuvchilar
            self.cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(last_active) = DATE('now')
            ''')
            stats['today_active'] = self.cursor.fetchone()[0]
            
            # Xabarlar soni
            self.cursor.execute('SELECT COUNT(*) FROM messages')
            stats['total_messages'] = self.cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistika olishda xato: {e}")
            return {}
    
    def cleanup_old_data(self, days=30):
        """Eski ma'lumotlarni tozalaydi"""
        try:
            # Eski chatlarni o'chirish
            self.cursor.execute('''
                DELETE FROM chats 
                WHERE ended_at IS NOT NULL 
                AND ended_at < datetime('now', ?)
            ''', (f'-{days} days',))
            
            # Eski takliflarni o'chirish
            self.cursor.execute('''
                DELETE FROM invitations 
                WHERE created_at < datetime('now', ?)
            ''', (f'-{days} days',))
            
            # Eski xabarlarni o'chirish
            self.cursor.execute('''
                DELETE FROM messages 
                WHERE sent_at < datetime('now', ?)
            ''', (f'-{days} days',))
            
            # Faolligi eskirgan foydalanuvchilarni o'chirish
            self.cursor.execute('''
                DELETE FROM users 
                WHERE last_active < datetime('now', ?)
            ''', (f'-{days*2} days',))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ma'lumotlarni tozalashda xato: {e}")
            return False
    
    def close(self):
        """Database ni yopadi"""
        if self.conn:
            self.conn.close()

# Global database obyekti
db = Database()
