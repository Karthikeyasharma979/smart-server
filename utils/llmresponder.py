from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def _build_docqa_prompt(context, query):
    return f"""
    You are an expert, highly accurate document analysis assistant. Your sole purpose is to answer the user's question relying **exclusively** on the provided document context.

    Strict Guidelines:
    1. EXCLUSIVE SOURCE: Use only the provided "Document Context" to formulate your answer. Do not incorporate any outside knowledge or assumptions.
    2. ABSENCE OF INFORMATION: If the provided context does not contain the information required to answer the question, you MUST reply with this exact phrase: "I cannot find the answer to that question in the provided document." Do not attempt to guess or provide partial answers based on speculation.
    3. CONCISE & CLEAR: Provide direct, concise answers without unnecessary filler.
    4. FORMATTING: Structure your answer using Markdown for enhanced readability. Use **bold** text to emphasize key terms or concepts, and use bullet points (-) or numbered lists for sequential or multiple items.

    --- Document Context ---
    \"\"\"{context}\"\"\"

    --- User Question ---
    {query}
    """


def _build_docqa_system_prompt(context):
    return f"""
    You are an expert, highly accurate document analysis assistant. Your sole purpose is to answer the user's question relying **exclusively** on the provided document context.

    Strict Guidelines:
    1. EXCLUSIVE SOURCE: Use only the provided "Document Context" to formulate your answer. Do not incorporate any outside knowledge or assumptions.
    2. ABSENCE OF INFORMATION: If the provided context does not contain the information required to answer the question, you MUST reply with this exact phrase: "I cannot find the answer to that question in the provided document." Do not attempt to guess or provide partial answers based on speculation.
    3. CONCISE & CLEAR: Provide direct, concise answers without unnecessary filler.
    4. FORMATTING: Structure your answer using Markdown for enhanced readability. Use **bold** text to emphasize key terms or concepts, and use bullet points (-) when listing multiple points.

    --- Document Context ---
    \"\"\"{context}\"\"\"
    """

def get_response_from_gemini(context, query):
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    prompt = _build_docqa_prompt(context, query)

    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def get_response_from_cohere_rag(context, query):
    client = OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=os.getenv("GITHUB_TOKEN"),
    )

    system_prompt = _build_docqa_system_prompt(context)

    response = client.chat.completions.create(
        model="cohere/Cohere-command-r-plus-08-2024",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.2,
        max_tokens=2048,
        top_p=0.9
    )
    return response.choices[0].message.content.strip()


def get_response_from_docqa_model(context, query):
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            return get_response_from_cohere_rag(context, query)
        except Exception:
            pass

    return get_response_from_gemini(context, query)
