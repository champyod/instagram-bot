import time
import random
import os
import sys
from datetime import datetime
from google import genai
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import config

# --- Configuration & Setup ---

SESSION_FILE = "ig_session.json"

# Configure Gemini Client
# The client automatically loads the API key from environment variables (GEMINI_API_KEY or GOOGLE_API_KEY)
# But we can also pass it explicitly if needed.
client = genai.Client(api_key=config.GEMINI_API_KEY)

def log(message):
    """Prints a message with a timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def human_like_delay(min_seconds=5, max_seconds=15):
    """Sleeps for a random amount of time to simulate human thinking."""
    delay = random.uniform(min_seconds, max_seconds)
    log(f"Thinking... sleeping for {delay:.2f} seconds.")
    time.sleep(delay)

def typing_simulation_delay(text_length):
    """Sleeps based on the length of the response to simulate typing."""
    # Assume roughly 0.1 to 0.3 seconds per character for realistic typing
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
    """Generates a response using Gemini with the specific persona."""
    
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
        return "เออ เดี๋ยวมาตอบนะ (AI Error)" # Fallback message

def run_bot():
    cl = Client()
    
    if not login(cl):
        log("Critical: Could not log in. Exiting.")
        return

    my_pk = str(cl.user_id)
    log(f"Bot started. User ID: {my_pk}")
    log(f"Target Users (Must verify these are USERNAMES not display names): {config.TARGET_USERS}")

    while True:
        try:
            # Polling interval set to 10 seconds as requested
            poll_interval = 10
            
            # --- Check Direct Threads ---
            threads = cl.direct_threads(amount=20)
            log(f"--- Checking {len(threads)} recent threads ---")
            
            for thread in threads:
                # Fix: Use 'messages' instead of 'items'
                last_msg = thread.messages[0] if thread.messages else None
                
                if not last_msg:
                    continue

                sender_pk = str(last_msg.user_id)
                message_text = last_msg.text if last_msg.item_type == 'text' else f"[{last_msg.item_type}]"
                
                # Identify Sender Username
                sender_username = "Unknown"
                for user in thread.users:
                    if str(user.pk) == sender_pk:
                        sender_username = user.username
                        break
                if sender_pk == my_pk:
                    sender_username = "Me (Bot)"

                # Get all participants (excluding bot) for logging clarity
                participants = [u.username for u in thread.users if str(u.pk) != my_pk]
                participants_str = ", ".join(participants)

                # Detailed Log for this thread
                is_from_me = (sender_pk == my_pk)
                status_icon = "✅ Read" if is_from_me else "📩 UNREAD"
                log(f"Thread: {thread.thread_title} [{participants_str}] | Last: {sender_username}: '{message_text[:20]}...' | {status_icon}")

                # Check for Kill Switch from Admin
                # Workaround: find admin PK from thread users to avoid buggy user_id_from_username call
                is_admin_sender = False
                for user in thread.users:
                    if user.username == config.ADMIN_USERNAME and str(user.pk) == sender_pk:
                        is_admin_sender = True
                        break
                
                if is_admin_sender:
                    if last_msg.item_type == 'text' and last_msg.text.strip() == "!stop":
                        log("🛑 Kill switch activated by Admin. Terminating...")
                        sys.exit(0)

                # Check if the thread involves one of our targets
                is_target = False
                target_username = ""
                
                for user in thread.users:
                    if user.username in config.TARGET_USERS:
                        is_target = True
                        target_username = user.username
                        break
                
                if is_target:
                     # Check if the last message is from the target (not from us)
                     if not is_from_me:
                        
                        log(f"✨ Target Match: {target_username}. Processing response...")
                        
                        # Start of anti-bot formatting
                        # log("Status: Unread message detected. Processing...") # Redundant

                        # 1. Human-like delay (Thinking)
                        # Reduced delay to 1-5 seconds as requested
                        human_like_delay(1, 5)
                        
                        # 2. Geneate Response
                        response_text = generate_response(message_text)
                        log(f"Generated response: {response_text}")
                        
                        # 3. Typing Simulation
                        typing_simulation_delay(len(response_text))
                        
                        # 4. Send Response
                        cl.direct_send(response_text, thread_ids=[thread.pk])
                        log(f"Sent response to {target_username}.")
                        
                        # 5. Mark as seen (to clear notification and maybe help logic if we expanded it)
                        # cl.direct_thread_mark_seen(thread.pk) # Optional, but good practice
            
            log(f"Sleeping for {poll_interval} seconds...")
            time.sleep(poll_interval)
            
        except LoginRequired:
            log("Session expired. Relogging...")
            login(cl)
        except Exception as e:
            log(f"An error occurred in main loop: {e}")
            log("Waiting 60 seconds before retrying...")
            time.sleep(60)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        log("Bot stopped manually.")
