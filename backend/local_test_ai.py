import os
import sys

# Ensure 'app' module can be found. Assuming script is in 'backend/'
sys.path.append(os.getcwd())

from app.services.llm_service import LLMService

def test_ai():
    print("Initializing LLM Service...")
    service = LLMService()
    
    if not service.model:
        print("ERROR: Model not initialized. Check API Key configuration.")
        return

    print("Model initialized. Sending test prompt...")
    prompt = "I want to check for SQL injection vulnerabilities in my login page."
    
    try:
        result = service.analyze_intent(prompt)
        print("\n--- Analysis Result ---")
        print(result)
        print("-----------------------")
    except Exception as e:
        print(f"\nERROR during analysis: {e}")

if __name__ == "__main__":
    # Simulate Env Vars if not set (User provided key in previous turn)
    if "GEMINI_API_KEY" not in os.environ:
        print("Setting temporary GEMINI_API_KEY for test...")
        # Using the key visible in the user's previous error message
        os.environ["GEMINI_API_KEY"] = "AIzaSyBo3N1sj5Y1S-SJ_yfRI9MERK6HsKzTBis"
    
    test_ai()
