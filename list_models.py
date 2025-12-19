from google import genai
import config
import os

client = genai.Client(api_key=config.GEMINI_API_KEY)

print("Listing available models...")
try:
    # API style might differ slightly in google-genai vs google-generativeai
    # The error message suggested Call ListModels.
    # checking SDK docs pattern: client.models.list()
    for model in client.models.list():
        print(f"- {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
