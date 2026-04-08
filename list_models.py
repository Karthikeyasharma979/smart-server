import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    try:
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        for model in models:
            print(f"Model: {model.name}")
    except Exception as e:
        print(f"Failed with error: {e}")

if __name__ == "__main__":
    list_models()
