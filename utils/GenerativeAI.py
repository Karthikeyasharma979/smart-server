from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)

# Initialize client lazily or globally if env is ready
# Ideally, we should initialize it once.
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("open_router")
        if not api_key:
            logger.warning("OPEN_ROUTER_API_KEY (open_router) not found in environment variables.")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client

def chat(text, tone, model="meta-llama/llama-3.2-3b-instruct:free"):
    client = get_client()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": f"Rewrite the following text to have a {tone} tone. Keep the meaning but adjust the style. Return ONLY the rewritten text without any introductory or concluding remarks.\n\nOriginal Text:\n{text}"
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in GenerativeAI chat: {e}")
        raise e
