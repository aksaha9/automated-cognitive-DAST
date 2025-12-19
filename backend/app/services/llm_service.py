from app.core.config import get_settings
from app.models import ScanType
import google.generativeai as genai
import json

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.setup_provider()

    def setup_provider(self):
        self.model = None
        if self.settings.ai_provider == 'google':
            if not self.settings.ai_api_key or self.settings.ai_api_key == "your_api_key_here":
                print("Warning: No API Key found for Gemini. Using Mock Mode.")
                return
            genai.configure(api_key=self.settings.ai_api_key)
            self.model = genai.GenerativeModel(self.settings.ai_model)

    def analyze_intent(self, user_prompt: str):
        """
        Analyzes the natural language prompt and returns a structured scan configuration.
        """
        # Mock Response for Testing/Demo if no key provided
        if not self.model:
            print("Processing in Mock Mode")
            # Simple keyword matching for demo purposes
            checks = []
            if "sql" in user_prompt.lower(): checks.append("SQL Injection")
            if "xss" in user_prompt.lower() or "script" in user_prompt.lower(): checks.append("XSS")
            if "csrf" in user_prompt.lower(): checks.append("CSRF")
            if "file" in user_prompt.lower() or "traversal" in user_prompt.lower(): checks.append("Path Traversal")
            
            if not checks: checks = ["SQL Injection", "XSS"] # Default
            
            return {
                "scan_type": "API" if "api" in user_prompt.lower() else "WEB",
                "checks": checks,
                "reasoning": "Simulated AI Analysis (Mock Mode): Detected relevant keywords in your prompt."
            }

        system_instruction = """
        You are an Application Security Expert. Your job is to translate a user's natural language security requirement into a structured DAST scan configuration.
        
        The user will describe their application or their security concerns.
        You must return a JSON object with the following fields:
        - scan_type: "WEB" or "API"
        - checks: A list of strings selected from ["SQL Injection", "XSS", "CSRF", "Path Traversal"].
        - reasoning: A brief explanation of why you chose these checks.

        Rules:
        - If the user mentions "API", "Service", "Endpoint", "REST", or "GraphQL", set scan_type to "API". Otherwise default to "WEB".
        - Map their concerns to the checks:
          - "Database", "Sequel", "SQL" -> "SQL Injection"
          - "Scripting", "Frontend attack", "Client-side" -> "XSS"
          - "Session", "State change", "Forged" -> "CSRF"
          - "File access", "Directory", "Local file" -> "Path Traversal"
        - If the prompt is generic (e.g., "Full scan"), include all checks.
        
        Return ONLY valid JSON. Do not wrap in markdown code blocks.
        """
        
        full_prompt = f"{system_instruction}\n\nUser Request: {user_prompt}\nJSON Response:"
        
        try:
            if self.settings.ai_provider == 'google':
                response = self.model.generate_content(full_prompt)
                # Clean up if the model includes markdown formatting
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                elif text.startswith("```"):
                    text = text[3:-3]
                
                return json.loads(text)
            
            # Mock or fallback for other providers not fully implemented yet
            return {
                "scan_type": "WEB",
                "checks": ["SQL Injection", "XSS"],
                "reasoning": "Provider not configured, returning default safe scan."
            }

        except Exception as e:
            print(f"LLM Analysis failed: {e}")
            # Fallback on failure
            return {
                "scan_type": "WEB",
                "checks": [],
                "reasoning": "AI Analysis failed. Please configure settings manually."
            }
