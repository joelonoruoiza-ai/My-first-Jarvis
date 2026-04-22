import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-1.5-flash')

try:
    response = model.generate_content("Say 'Systems Online' if you can hear me.")
    print(f"Gemini says: {response.text}")
except Exception as e:
    print(f"Error: {e}")