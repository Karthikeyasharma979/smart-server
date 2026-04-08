import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, this is a test. Please respond with 'New SDK working'."
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Failed with error: {e}")

if __name__ == "__main__":
    test_gemini()
