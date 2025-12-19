import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

IG_USERNAME = os.getenv('IG_USERNAME')
IG_PASSWORD = os.getenv('IG_PASSWORD')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Parse target users from comma-separated string
target_users_str = os.getenv('TARGET_USERS', '')
TARGET_USERS = [user.strip() for user in target_users_str.split(',') if user.strip()]

if not all([IG_USERNAME, IG_PASSWORD, ADMIN_USERNAME, GEMINI_API_KEY]):
    print("WARNING: Some environment variables are missing. Please check .env file.")
