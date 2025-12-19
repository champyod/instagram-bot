import time
import random
import os
import sys
import math
import argparse
from datetime import datetime, timedelta
from google import genai
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import config

# Rich Imports
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.table import Table

# --- Configuration & Setup ---

import json

# --- Configuration & Setup ---

SESSION_FILE = "ig_session.json"
TARGETS_FILE = "targets.json"
client = genai.Client(api_key=config.GEMINI_API_KEY)

def load_targets():
    """Load targets from JSON file, falling back to config.py if not exists."""
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            log(f"Error loading targets file: {e}")
    
    # Fallback to env config and save it
    initial_targets = config.TARGET_USERS
    save_targets(initial_targets)
    return initial_targets

def save_targets(targets):
    """Save target list to JSON file."""
    try:
        with open(TARGETS_FILE, 'w') as f:
            json.dump(targets, f, indent=4)
    except Exception as e:
        log(f"Error saving targets file: {e}")

# --- Global TUI State ---
class BotTUI:
    def __init__(self, use_tui=False):
        self.use_tui = use_tui
        self.console = Console()
        self.logs = []  # Store last N logs for TUI
        self.recent_threads = [] # Store thread data
        self.status_msg = "Starting..."
        self.user_id = "Unknown"
        self.targets = load_targets()
        self.paused = False
        self.ignore_until = None
        self.user_ignore_timers = {} # {username: datetime_expiry}
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {message}"
        
        if self.use_tui:
            self.logs.append(full_msg)
            if len(self.logs) > 50: # Keep last 50 logs
                self.logs.pop(0)
        else:
            print(full_msg)
            
    def update_threads(self, thread_list):
        self.recent_threads = thread_list

    def set_status(self, msg, paused=False, ignore_until=None):
        self.status_msg = msg
        self.paused = paused
        self.ignore_until = ignore_until

    def add_target(self, username):
        if username not in self.targets:
            self.targets.append(username)
            save_targets(self.targets)
            return True
        return False

    def remove_target(self, username):
        if username in self.targets:
            self.targets.remove(username)
            save_targets(self.targets)
            return True
        return False
        
    def ignore_user(self, username, minutes):
        self.user_ignore_timers[username] = datetime.now() + timedelta(minutes=minutes)

    def is_user_ignored(self, username):
        if username in self.user_ignore_timers:
            if datetime.now() < self.user_ignore_timers[username]:
                return True
            else:
                del self.user_ignore_timers[username] # Expired
        return False

    def set_mode(self, mode):
        self.mode = mode
        save_mode(mode) # Optional: persist mode if desired, or just keep runtime

    def generate_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3) # Will be dynamic
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )
        
        # Header
        status_color = "red" if self.paused else "green"
        mode_icon = "😈" if self.mode == "default" else ("😇" if self.mode == "polite" else "🤡")
        header_text = f"🤖 Instagram Bot | User: {self.user_id} | Mode: {self.mode.upper()} {mode_icon} | Status: [{status_color}]{self.status_msg}[/{status_color}]"
        layout["header"].update(Panel(header_text, style="bold white on blue"))
        
        # Logs (Right)
        log_text = "\n".join(self.logs)
        layout["right"].update(Panel(log_text, title="📜 Recent Logs", border_style="cyan"))
        
        # Threads (Left)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Thread", style="dim", width=20)
        table.add_column("Last Msg", width=30)
        table.add_column("Status", justify="right")
        
        for t in self.recent_threads[:15]: # Show top 15
            table.add_row(t['title'], t['msg'], t['status'])
            
        layout["left"].update(Panel(table, title="💬 Recent Threads", border_style="green"))
        
        # Footer
        targets_list = self.targets
        targets_str = ", ".join(targets_list)
        footer_text = f"Targets: {targets_str} | !polite, !joke, !normal, !add/remove | [Ctrl+C to Stop]"
        
        available_width = max(10, self.console.width - 4)
        required_lines = math.ceil(len(footer_text) / available_width)
        layout["footer"].size = required_lines + 2
        layout["footer"].update(Panel(footer_text, style="white on black"))
        
        return layout

# Global instance
BOT_UI = None

def log(message):
    """Wrapper to use global BOT_UI logger"""
    if BOT_UI:
        BOT_UI.log(message)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

def human_like_delay(min_seconds=5, max_seconds=15):
    """Sleeps for a random amount of time."""
    delay = random.uniform(min_seconds, max_seconds)
    log(f"Thinking... sleeping for {delay:.2f} seconds.")
    time.sleep(delay)

def typing_simulation_delay(text_length):
    """Sleeps based on response length."""
    delay = text_length * random.uniform(0.1, 0.2)
    delay = max(1.0, min(delay, 10.0))
    log(f"Typing... sleeping for {delay:.2f} seconds.")
    time.sleep(delay)

def login(cl):
    """Handles login."""
    if os.path.exists(SESSION_FILE):
        log("Session file found. Attempting to load session...")
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(config.IG_USERNAME, config.IG_PASSWORD)
            log("Logged in successfully using session.")
            return True
        except Exception as e:
            log(f"Session load failed: {e}. Trying fresh login...")
    
    log("Attempting fresh login...")
    try:
        cl.login(config.IG_USERNAME, config.IG_PASSWORD)
        log("✅ LOGIN SUCCESSFUL (Credentials)")
        cl.dump_settings(SESSION_FILE)
        log("Session file saved.")
        return True
    except Exception as e:
        log(f"❌ Login failed: {e}")
        return False

def generate_response(prompt_input):
    """Generates a response using Gemini based on current mode."""
    
    current_mode = BOT_UI.mode if BOT_UI else "default"
    
    if current_mode == "polite":
        persona_instruction = (
            "You are a polite, respectful, and helpful Thai assistant. "
            "Use formal/polite language (end with ครับ/ค่ะ when appropriate). "
            "Be kind and avoid slang or rude words. "
            "Keep the response VERY SHORT, NOT EXCEEDING 1 SENTENCE. "
        )
    elif current_mode == "joke":
        # Specific instruction: Funny but NOT insulating/rude
        persona_instruction = (
            "You are a funny, cheerful Thai friend who loves telling jokes. "
            "Make a joke or say something funny based on the input. "
            "IMPORTANT: Be lighthearted and playful. "
            "Do NOT be sarcastic, rude, insulting, or aggressive. "
            "Do NOT use profanity. "
            "Keep the response VERY SHORT, NOT EXCEEDING 1 SENTENCE. "
        )
    else: # Default (Kwan-teen)
        persona_instruction = (
            "You are a creative, sarcastic, and 'kwan-teen' (กวนตีน) Thai friend. "
            "Use Thai slang, be witty, and avoid repetitive answers. "
            "Keep the response VERY SHORT, NOT EXCEEDING 1 SENTENCE. "
            "Do not use profanity (คำหยาบ) unless the user uses it first."
        )

    full_prompt = persona_instruction + "The user said: " + prompt_input
    
    try:
        models_list = ['gemini-3-flash-preview', 'gemini-2.5-flash-lite-preview-09-2025']
        selected_model = random.choice(models_list)
        
        response = client.models.generate_content(
            model=selected_model,
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        log(f"Gemini API Error: {e}")
        return "เออ เดี๋ยวมาตอบนะ (AI Error)"

def run_bot(use_tui=False, start_mode="default"):
    global BOT_UI
    BOT_UI = BotTUI(use_tui)
    BOT_UI.mode = start_mode # Set initial mode
    
    if use_tui:
        with Live(BOT_UI.generate_layout(), refresh_per_second=4, screen=True) as live:
            _run_bot_logic(live)
    else:
        _run_bot_logic(None)

def _run_bot_logic(live_ctx):
    cl = Client()
    
    if not login(cl):
        log("Critical: Could not log in. Exiting.")
        return

    my_pk = str(cl.user_id)
    if BOT_UI: BOT_UI.user_id = my_pk
    
    log(f"Bot started. User ID: {my_pk} targets: {len(BOT_UI.targets)}")
    log(f"Initial Mode: {BOT_UI.mode}")

    is_paused = False
    ignore_until = None

    while True:
        try:
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())

            if ignore_until and datetime.now() > ignore_until:
                log("⏳ Ignore timer expired. Resuming bot...")
                ignore_until = None
                is_paused = False

            poll_interval = 10
            
            status_text = "Running"
            if is_paused:
                status_text = "⛔ PAUSED"
                if ignore_until:
                    remaining = (ignore_until - datetime.now()).total_seconds() / 60
                    status_text += f" (Resuming in {remaining:.1f} mins)"
            
            if BOT_UI: BOT_UI.set_status(status_text, is_paused, ignore_until)
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())
            
            threads = cl.direct_threads(amount=20)
            log(f"--- Checking {len(threads)} recent threads ---")
            
            tui_thread_list = []

            for thread in threads:
                last_msg = thread.messages[0] if thread.messages else None
                if not last_msg: continue

                sender_pk = str(last_msg.user_id)
                message_text = last_msg.text if last_msg.item_type == 'text' else f"[{last_msg.item_type}]"
                
                sender_username = "Unknown"
                for user in thread.users:
                    if str(user.pk) == sender_pk:
                        sender_username = user.username
                        break
                if sender_pk == my_pk:
                    sender_username = "Me"

                participants = [u.username for u in thread.users if str(u.pk) != my_pk]
                participants_str = ", ".join(participants)
                
                is_from_me = (sender_pk == my_pk)
                status_icon = "✅" if is_from_me else "📩"
                log_status = "Read" if is_from_me else "UNREAD"
                
                tui_thread_list.append({
                    "title": f"{thread.thread_title} [{participants_str}]",
                    "msg": f"{sender_username}: {message_text[:15]}...",
                    "status": f"{status_icon} {log_status}"
                })

                log(f"Thread: {thread.thread_title} [{participants_str}] | Last: {sender_username}: '{message_text[:20]}...' | {status_icon} {log_status}")

                # Admin Check
                is_admin_sender = False
                for user in thread.users:
                    if user.username == config.ADMIN_USERNAME and str(user.pk) == sender_pk:
                        is_admin_sender = True
                        break
                
                if is_admin_sender and last_msg.item_type == 'text':
                    cmd = last_msg.text.strip().lower()
                    parts = cmd.split()
                    
                    if cmd == "!kill":
                        log("🛑 Kill switch (!kill) activated.")
                        sys.exit(0)
                        
                    elif cmd == "!stop":
                        if not is_paused:
                            log("⏸️ Admin sent stop. Bot PAUSED.")
                            is_paused = True
                            ignore_until = None
                            cl.direct_send("Bot Paused ⏸️", thread_ids=[thread.pk])
                            
                    elif cmd == "!start":
                        if is_paused:
                            log("▶️ Admin sent start. Bot RESUMED.")
                            is_paused = False
                            ignore_until = None
                            cl.direct_send("Bot Resumed ▶️", thread_ids=[thread.pk])
                    
                    # Mode Switch Commands
                    elif cmd == "!polite":
                        BOT_UI.mode = "polite"
                        log("😇 Mode changed to POLITE")
                        cl.direct_send("Mode: Polite 😇", thread_ids=[thread.pk])
                        
                    elif cmd == "!joke":
                        BOT_UI.mode = "joke"
                        log("🤡 Mode changed to JOKE")
                        cl.direct_send("Mode: Joke 🤡", thread_ids=[thread.pk])

                    elif cmd in ["!normal", "!default", "!reset"]:
                        BOT_UI.mode = "default"
                        log("😈 Mode changed to DEFAULT")
                        cl.direct_send("Mode: Default (Kwan-teen) 😈", thread_ids=[thread.pk])

                    elif parts[0] == "!ignore":
                        try:
                            if len(parts) == 2:
                                mins = float(parts[1])
                                ignore_until = datetime.now() + timedelta(minutes=mins)
                                is_paused = True
                                log(f"⏳ Admin sent !ignore {mins}.")
                                cl.direct_send(f"Sleeping for {mins} mins ⏳", thread_ids=[thread.pk])
                            elif len(parts) == 3:
                                target_p = parts[1]
                                mins = float(parts[2])
                                BOT_UI.ignore_user(target_p, mins)
                                log(f"⏳ Ignoring {target_p} for {mins} mins.")
                                cl.direct_send(f"Ignoring {target_p} for {mins} mins ⏳", thread_ids=[thread.pk])
                        except ValueError:
                            cl.direct_send("⚠️ Error: Check format", thread_ids=[thread.pk])

                    elif parts[0] == "!add" and len(parts) > 1:
                        new_user = parts[1]
                        if BOT_UI.add_target(new_user):
                            log(f"✅ Added {new_user}.")
                            cl.direct_send(f"Added {new_user} ✅", thread_ids=[thread.pk])
                        else:
                            cl.direct_send(f"{new_user} exists or failed.", thread_ids=[thread.pk])

                    elif parts[0] == "!remove" and len(parts) > 1:
                        rem_user = parts[1]
                        if BOT_UI.remove_target(rem_user):
                            log(f"🗑️ Removed {rem_user}.")
                            cl.direct_send(f"Removed {rem_user} 🗑️", thread_ids=[thread.pk])
                        else:
                            cl.direct_send(f"{rem_user} not found.", thread_ids=[thread.pk])

                if is_paused: continue

                is_target = False
                target_username = ""
                for user in thread.users:
                    if user.username in BOT_UI.targets:
                        is_target = True
                        target_username = user.username
                        break
                
                if is_target:
                    if BOT_UI.is_user_ignored(target_username):
                         log(f"Skipping {target_username} (Ignored).")
                         continue
                         
                    if not is_from_me:
                        log(f"✨ Target Match: {target_username}. Processing...")
                        if live_ctx: live_ctx.update(BOT_UI.generate_layout())
                        
                        human_like_delay(1, 5)
                        response_text = generate_response(message_text)
                        typing_simulation_delay(len(response_text))
                        
                        cl.direct_send(response_text, thread_ids=[thread.pk])
                        log(f"Sent response to {target_username}.")
            
            if BOT_UI: BOT_UI.update_threads(tui_thread_list)
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())

            log(f"Sleeping for {poll_interval}s...")
            for _ in range(poll_interval):
                time.sleep(1)
                
        except LoginRequired:
            log("Session expired. Relogging...")
            login(cl)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tui", action="store_true", help="Enable TUI mode")
    parser.add_argument("-p", "--polite", action="store_true", help="Start in Polite Mode")
    parser.add_argument("-j", "--joke", action="store_true", help="Start in Joke Mode (No insults)")
    args = parser.parse_args()
    
    start_mode = "default"
    if args.polite:
        start_mode = "polite"
    elif args.joke:
        start_mode = "joke"
    
    try:
        run_bot(use_tui=args.tui, start_mode=start_mode)
    except KeyboardInterrupt:
        log("Bot stopped manually.")
