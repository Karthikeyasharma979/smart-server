import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostics")

def test_github():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GitHub: GITHUB_TOKEN MISSING")
        return False
    
    client = OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=token,
    )
    try:
        # Testing one common model
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("GitHub (openai/gpt-4o-mini): WORKING")
        return True
    except Exception as e:
        print(f"GitHub (openai/gpt-4o-mini): FAILED - {e}")
        return False

def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Groq: GROQ_API_KEY MISSING")
        return False
    
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )
    try:
        # Testing llama-3.1-8b-instant
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("Groq (llama-3.1-8b-instant): WORKING")
        return True
    except Exception as e:
        print(f"Groq (llama-3.1-8b-instant): FAILED - {e}")
        return False

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Gemini: GEMINI_API_KEY MISSING")
        return False
    
    # Using the old OpenAI compatible endpoint for simplicity in diagnostic
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key,
    )
    try:
        response = client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("Gemini (gemini-1.5-flash via OpenAI endpoint): WORKING")
        return True
    except Exception as e:
        print(f"Gemini (gemini-1.5-flash via OpenAI endpoint): FAILED - {e}")
        return False

if __name__ == "__main__":
    print("--- Running Diagnostics ---")
    test_github()
    test_groq()
    test_gemini()
    print("--- Diagnostics Complete ---")
