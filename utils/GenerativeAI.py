import os
import logging
import re
import difflib
from openai import OpenAI

logger = logging.getLogger(__name__)

# Groq available models
GROQ_MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

# GitHub available models (for summarization)
GITHUB_MODEL_CANDIDATES = [
    "openai/gpt-4o-mini",
    "meta/Llama-3.3-70B-Instruct",
]

MODEL_ALIASES = {
    "gemini-1.5-flash": "llama-3.1-8b-instant",
    "gemini-1.5-pro": "llama-3.3-70b-versatile",
}

TONE_PROFILES = {
    "professional": "formal business communication with precise, confident wording",
    "casual": "conversational and relaxed language that still stays clear",
    "academic": "scholarly, objective, and analytical writing with formal structure",
    "friendly": "warm, approachable, and positive language",
    "formal": "polite and structured formal language",
    "persuasive": "convincing language with clear calls to value",
    "concise": "shorter and tighter phrasing with no unnecessary words",
    "detailed": "expanded explanation with richer detail while preserving meaning",
    "simple": "easy-to-read plain language for broad audiences",
    "neutral": "clear and balanced wording without strong stylistic bias",
}

def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())

def _is_near_copy(source_text: str, rewritten_text: str) -> bool:
    source = _normalize_text(source_text)
    rewritten = _normalize_text(rewritten_text)
    if not source or not rewritten:
        return False
    if source == rewritten:
        return True
    return difflib.SequenceMatcher(None, source, rewritten).ratio() >= 0.9

def _build_prompt(text: str, tone: str) -> str:
    normalized_tone = (tone or "neutral").strip().lower()

    if normalized_tone in TONE_PROFILES:
        style_description = TONE_PROFILES[normalized_tone]
        return (
            "You are an expert writing editor.\n"
            "Task: Rewrite the provided text in the requested tone while preserving meaning.\n\n"
            f"Requested tone: {normalized_tone} ({style_description}).\n"
            "Hard requirements:\n"
            "- Keep all key facts and intent from the original text.\n"
            "- Change wording and sentence flow to clearly reflect the requested tone.\n"
            "- Do not add prefaces like 'Here is the rewrite'.\n"
            "- Return only the rewritten text.\n"
            "- Keep markdown only if it already exists in the source.\n\n"
            "Text to rewrite:\n"
            f"\"\"\"{text}\"\"\""
        )

    return (
        "You are an expert writing assistant.\n"
        "Task: Apply the instruction to the provided text and return the edited result only.\n\n"
        f"Instruction: {tone}\n"
        "Hard requirements:\n"
        "- Preserve the original intent unless the instruction explicitly asks otherwise.\n"
        "- Do not add assistant commentary or meta text.\n"
        "- Return only the transformed text.\n\n"
        "Text to transform:\n"
        f"\"\"\"{text}\"\"\""
    )

def _resolve_requested_model(requested_model: str) -> str:
    model = (requested_model or "").strip()
    if model in MODEL_ALIASES:
        return MODEL_ALIASES[model]
    if model in GROQ_MODEL_CANDIDATES:
        return model
    return GROQ_MODEL_CANDIDATES[0]

def _call_groq_model_with_fallback(groq_api_key: str, prompt: str, preferred_model: str) -> str:
    model_queue = []
    resolved_preferred = _resolve_requested_model(preferred_model)
    if resolved_preferred in GROQ_MODEL_CANDIDATES:
        model_queue.append(resolved_preferred)
    model_queue.extend([m for m in GROQ_MODEL_CANDIDATES if m not in model_queue])

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key,
    )

    last_error = None
    for candidate in model_queue:
        try:
            response = client.chat.completions.create(
                model=candidate,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )
            content = response.choices[0].message.content if response.choices else ""
            if content:
                return content
        except Exception as err:
            logger.warning(f"Groq model '{candidate}' request failed. Trying next candidate.")
            last_error = err
            continue

    if last_error:
        raise last_error
    raise RuntimeError("No compatible Groq model was available.")

def _local_fallback_response(text: str, tone: str) -> str:
    normalized_tone = (tone or "neutral").strip().lower()
    compact = " ".join((text or "").split())
    if not compact:
        return "Please provide a message so I can help."

    trimmed = compact[:700]
    prefixes = {
        "friendly": "Absolutely. Here is a friendly take:",
        "professional": "Certainly. Here is a professional response:",
        "creative": "Great prompt. Here is a creative response:",
        "academic": "Here is an academic-style response:",
    }
    prefix = prefixes.get(normalized_tone, "Here is a refined response:")
    return f"{prefix}\n\n{trimmed}"

def chat(text, tone, model="llama-3.1-8b-instant", use_github_fallback=False):
    normalized_tone = (tone or "neutral").strip().lower()
    prompt = _build_prompt(text=text, tone=normalized_tone)

    try:
        output = ""
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found. Falling back to local response.")
            return _local_fallback_response(text=text, tone=tone)

        # Attempt Groq model (user's preferred provider for this feature)
        try:
            output = _call_groq_model_with_fallback(
                groq_api_key=groq_api_key,
                prompt=prompt,
                preferred_model=model,
            ).strip()
        except Exception as groq_err:
            logger.error(f"Groq primary AI call failed: {groq_err}")

        # If tone transformation produced nearly unchanged text, force a stronger rewrite once.
        if output and normalized_tone != "neutral" and _is_near_copy(text, output):
            logger.warning("Tone rewrite too similar to input. Retrying with stronger Groq rewrite constraints.")
            retry_prompt = (
                f"Rewrite the following text again in a distinctly {normalized_tone} tone.\n"
                "Hard requirements:\n"
                "- Keep the same meaning and facts.\n"
                "- Use clearly different phrasing and sentence structure.\n"
                "- Return only the rewritten text.\n\n"
                f"Text:\n\"\"\"{text}\"\"\""
            )
            try:
                retry_output = _call_groq_model_with_fallback(
                    groq_api_key=groq_api_key,
                    prompt=retry_prompt,
                    preferred_model=model,
                ).strip()
                if retry_output:
                    output = retry_output
            except Exception as retry_err:
                logger.warning(f"Groq retry failed: {retry_err}")

        if output:
            return output
        
        return _local_fallback_response(text=text, tone=tone)
    except Exception as e:
        logger.error(f"Error in GenerativeAI chat: {e}")
        return _local_fallback_response(text=text, tone=tone)
