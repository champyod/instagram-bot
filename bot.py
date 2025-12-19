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

    def generate_layout(self):
        # Footer Content
        # Show more targets, but still truncate if extremely long to avoid taking up whole screen
        targets_list = self.targets
        targets_str = ", ".join(targets_list)
        footer_text = f"Targets: {targets_str} | !add, !remove, !ignore <user> n | [Press Ctrl+C to Stop]"
        
        # Calculate dynamic height for footer
        # Width available for text inside panel (approx console width - 4 for borders/padding)
        available_width = max(10, self.console.width - 4)
        required_lines = math.ceil(len(footer_text) / available_width)
        footer_height = required_lines + 2 # +2 for top/bottom borders
        
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=footer_height)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )
        
        # Header
        status_color = "red" if self.paused else "green"
        header_text = f"🤖 Instagram Bot | User: {self.user_id} | Status: [{status_color}]{self.status_msg}[/{status_color}]"
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
        
        # Footer Update
        layout["footer"].update(Panel(footer_text, style="white on black"))
        
        return layout

# Global instance
BOT_UI = None

def log(message):
    """Wrapper to use global BOT_UI logger"""
    if BOT_UI:
        BOT_UI.log(message)
    else:
        # Fallback if UI not init
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

def human_like_delay(min_seconds=5, max_seconds=15):
    """Sleeps for a random amount of time to simulate human thinking."""
    delay = random.uniform(min_seconds, max_seconds)
    log(f"Thinking... sleeping for {delay:.2f} seconds.")
    # In TUI mode, we might want to update the UI while sleeping? 
    # For simplicity, we just sleep, blocking the TUI update loop briefly unless we threaded it.
    # But since we update TUI in the main loop, small sleeps are fine. 
    # For better UX, we could chunk the sleep.
    time.sleep(delay)

def typing_simulation_delay(text_length):
    """Sleeps based on the length of the response to simulate typing."""
    delay = text_length * random.uniform(0.1, 0.2)
    # Cap the delay as requested (1-10 seconds)
    delay = max(1.0, min(delay, 10.0))
    log(f"Typing... sleeping for {delay:.2f} seconds.")
    time.sleep(delay)

def login(cl):
    """Handles login with session file or credentials."""
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
    """Generates a response using Gemini."""
    persona_instruction = (
        "You are a creative, sarcastic, and 'kwan-teen' (กวนตีน) Thai friend. "
        "Use Thai slang, be witty, and avoid repetitive answers. "
        "Keep the response VERY SHORT, NOT EXCEEDING 1 SENTENCE. "
        "Do not use profanity (คำหยาบ) unless the user uses it first."
        "The user said: "
    )
    full_prompt = persona_instruction + prompt_input
    
    try:
        # Rotation models to avoid rate limits
        models_list = ['gemini-3-flash-preview', 'gemini-2.5-flash-lite-preview-09-2025']
        selected_model = random.choice(models_list)
        
        # log(f"Using AI Model: {selected_model}") # Optional debug log

        response = client.models.generate_content(
            model=selected_model,
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        log(f"Gemini API Error: {e}")
        return "เออ เดี๋ยวมาตอบนะ (AI Error)"

def run_bot(use_tui=False):
    global BOT_UI
    BOT_UI = BotTUI(use_tui)
    
    # If TUI is on, we need a Live context. 
    # But `login` might happen before.
    # We'll use a wrapper generator logic or just handle TUI update manually inside loop if use_tui logic permits.
    # Actually rich.Live is a context manager.
    
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
    log("Admin commands loaded.")

    is_paused = False
    ignore_until = None

    while True:
        try:
            # Refresh TUI
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())

            # Check ignore timer
            if ignore_until and datetime.now() > ignore_until:
                log("⏳ Ignore timer expired. Resuming bot...")
                ignore_until = None
                is_paused = False

            poll_interval = 10
            
            # Update Status text
            status_text = "Running"
            if is_paused:
                status_text = "⛔ PAUSED"
                if ignore_until:
                    remaining = (ignore_until - datetime.now()).total_seconds() / 60
                    status_text += f" (Resuming in {remaining:.1f} mins)"
            
            if BOT_UI: BOT_UI.set_status(status_text, is_paused, ignore_until)
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())
            
            # --- Check Direct Threads ---
            threads = cl.direct_threads(amount=20)
            log(f"--- Checking {len(threads)} recent threads ---")
            
            # Build thread data for TUI
            tui_thread_list = []

            for thread in threads:
                last_msg = thread.messages[0] if thread.messages else None
                if not last_msg: continue

                sender_pk = str(last_msg.user_id)
                message_text = last_msg.text if last_msg.item_type == 'text' else f"[{last_msg.item_type}]"
                
                # Identify Sender Username
                sender_username = "Unknown"
                for user in thread.users:
                    if str(user.pk) == sender_pk:
                        sender_username = user.username
                        break
                if sender_pk == my_pk:
                    sender_username = "Me"

                # Helper for logging
                participants = [u.username for u in thread.users if str(u.pk) != my_pk]
                participants_str = ", ".join(participants)
                
                is_from_me = (sender_pk == my_pk)
                status_icon = "✅" if is_from_me else "📩"
                log_status = "Read" if is_from_me else "UNREAD"
                
                # Add to TUI list
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
                            log("⏸️ Admin sent !stop. Bot PAUSED.")
                            is_paused = True
                            ignore_until = None
                            cl.direct_send("Bot Paused ⏸️", thread_ids=[thread.pk])
                            
                    elif cmd == "!start":
                        if is_paused:
                            log("▶️ Admin sent !start. Bot RESUMED.")
                            is_paused = False
                            ignore_until = None
                            cl.direct_send("Bot Resumed ▶️", thread_ids=[thread.pk])
                            
                    # !ignore <n> OR !ignore <username> <n>
                    elif parts[0] == "!ignore":
                        # Cases: 
                        # 1. !ignore 10  (Global pause)
                        # 2. !ignore username 10 (Target pause)
                        
                        try:
                            if len(parts) == 2:
                                # Case 1: Global
                                mins = float(parts[1])
                                ignore_until = datetime.now() + timedelta(minutes=mins)
                                is_paused = True
                                log(f"⏳ Admin sent !ignore {mins}.")
                                cl.direct_send(f"Sleeping for {mins} mins ⏳", thread_ids=[thread.pk])
                                
                            elif len(parts) == 3:
                                # Case 2: Target
                                target_p = parts[1]
                                mins = float(parts[2])
                                BOT_UI.ignore_user(target_p, mins)
                                log(f"⏳ Ignoring {target_p} for {mins} mins.")
                                cl.direct_send(f"Ignoring {target_p} for {mins} mins ⏳", thread_ids=[thread.pk])
                        except ValueError:
                            cl.direct_send("⚠️ Error: Check format !ignore [user] n", thread_ids=[thread.pk])

                    elif parts[0] == "!add" and len(parts) > 1:
                        new_user = parts[1]
                        if BOT_UI.add_target(new_user):
                            log(f"✅ Added {new_user} to targets.")
                            cl.direct_send(f"Added {new_user} ✅", thread_ids=[thread.pk])
                        else:
                            cl.direct_send(f"{new_user} already in targets.", thread_ids=[thread.pk])

                    elif parts[0] == "!remove" and len(parts) > 1:
                        rem_user = parts[1]
                        if BOT_UI.remove_target(rem_user):
                            log(f"🗑️ Removed {rem_user} from targets.")
                            cl.direct_send(f"Removed {rem_user} 🗑️", thread_ids=[thread.pk])
                        else:
                            cl.direct_send(f"{rem_user} not found.", thread_ids=[thread.pk])

                if is_paused: continue

                # Target Check
                is_target = False
                target_username = ""
                for user in thread.users:
                    if user.username in BOT_UI.targets:
                        is_target = True
                        target_username = user.username
                        break
                
                if is_target:
                    # Check per-user ignore
                    if BOT_UI.is_user_ignored(target_username):
                         log(f"Skipping {target_username} (Ignored).")
                         continue
                         
                    if not is_from_me:
                        log(f"✨ Target Match: {target_username}. Processing...")
                        if live_ctx: live_ctx.update(BOT_UI.generate_layout()) # Update UI before delay
                        
                        human_like_delay(1, 5)
                        response_text = generate_response(message_text)
                        typing_simulation_delay(len(response_text))
                        
                        cl.direct_send(response_text, thread_ids=[thread.pk])
                        log(f"Sent response to {target_username}.")
            
            # Update UI with thread list
            if BOT_UI: BOT_UI.update_threads(tui_thread_list)
            if live_ctx: live_ctx.update(BOT_UI.generate_layout())

            log(f"Sleeping for {poll_interval}s...")
            # Sleep in chunks to allow Ctrl+C
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
    args = parser.parse_args()
    
    try:
        run_bot(use_tui=args.tui)
    except KeyboardInterrupt:
        log("Bot stopped manually.")
