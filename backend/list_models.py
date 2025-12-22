import os
import sys
import google.generativeai as genai

KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBo3N1sj5Y1S-SJ_yfRI9MERK6HsKzTBis")
genai.configure(api_key=KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
