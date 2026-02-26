import os
import requests
import logging

logger = logging.getLogger(__name__)

def chat(text, tone, model="gemini-2.5-flash"):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables.")
        raise ValueError("GEMINI_API_KEY missing")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": (
                f"You are a highly capable and intelligent AI assistant. You must respond to the user's input while adopting a strictly '{tone}' tone and persona.\n\n"
                f"Guidelines:\n"
                f"- Act purely as the persona '{tone}'.\n"
                f"- Direct Action: If the user asks you to write, draft, or brainstorm something, DO NOT provide templates, explanations, or conversational filler (e.g., 'Sure, I can help!', 'Here is a draft:'). Just provide the requested content directly.\n"
                f"- Adapt your vocabulary, sentence structure, and tone to perfectly match the '{tone}' persona.\n"
                f"- Use Markdown formatting naturally (such as bolding, bullet points, or code blocks) when it improves readability.\n\n"
                f"User Request:\n"
                f"\"\"\"{text}\"\"\""
            )}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        resp_json = response.json()
        
        # Extract content securely
        if "candidates" in resp_json and len(resp_json["candidates"]) > 0:
            parts = resp_json["candidates"][0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    return part["text"]
        
        return "Error: Could not generate content from the model."
    except Exception as e:
        logger.error(f"Error in GenerativeAI chat: {e}")
        raise e
