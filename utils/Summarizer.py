from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")
        _client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
    return _client

def summary(text: str, length="medium", format_type="paragraph"):
    client = get_client()
    
    length_instruction = "concise" if length == "short" else "detailed" if length == "long" else "moderate length"
    format_instruction = "a bulleted list. Use a new line for each point. Start each point with a '•' character" if "bullet" in format_type.lower() or "point" in format_type.lower() else "paragraph"

    prompt = (
        f"You are an expert summarization assistant. Your task is to extract the core ideas and critical details from the provided text.\n\n"
        f"Target Length: {length_instruction}\n"
        f"Output Format: {format_instruction}\n\n"
        f"Guidelines:\n"
        f"- Ensure the summary contains no hallucinations or external information.\n"
        f"- Maintain the original context and overall tone of the text.\n"
        f"- Return purely the requested summary without any conversational filler or introductions.\n\n"
        f"Text to Summarize:\n"
        f"\"\"\"{text}\"\"\""
    )

    try:
        completion = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in Summarizer: {e}")
        raise e