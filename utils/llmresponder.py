from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def get_response_from_gemini(context, query):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("open_router"),
    )
    
    prompt = f"""
    You are a strict document assistant. Your task is to answer the user's question using ONLY the provided document context.

    Rules:
    1. If the answer is found in the context, answer concisely.
    2. If the answer is NOT in the context, you must reply exactly: "I cannot find the answer to that question in the provided document."
    3. Do NOT use outside knowledge or hallucinate.
    4. Format the answer using Markdown for readability (use **bold** for key terms and - bullet points for lists).

    --- Document Context ---
    {context}

    --- User Question ---
    {query}
    """

    response = client.chat.completions.create(
        model="tngtech/deepseek-r1t2-chimera:free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()
