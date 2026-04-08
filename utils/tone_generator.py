import re
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for better performance
TONE_TRANSFORMATIONS = {
    'formal': {
        'replacements': {
            re.compile(r'\bcan\'t\b', re.IGNORECASE): 'cannot',
            re.compile(r'\bdon\'t\b', re.IGNORECASE): 'do not',
            re.compile(r'\bwon\'t\b', re.IGNORECASE): 'will not',
            re.compile(r'\bisn\'t\b', re.IGNORECASE): 'is not',
            re.compile(r'\bI think\b', re.IGNORECASE): 'I believe',
            re.compile(r'\bkinda\b', re.IGNORECASE): 'somewhat',
            re.compile(r'\bgonna\b', re.IGNORECASE): 'going to',
            re.compile(r'\bwanna\b', re.IGNORECASE): 'want to',
            re.compile(r'\bhey\b', re.IGNORECASE): 'hello',
            re.compile(r'\byeah\b', re.IGNORECASE): 'yes'
        },
        'prefix': 'I would like to respectfully present the following: ',
        'suffix': ' I hope this information proves valuable.'
    },
    'casual': {
        'replacements': {
            re.compile(r'\bcannot\b', re.IGNORECASE): 'can\'t',
            re.compile(r'\bdo not\b', re.IGNORECASE): 'don\'t',
            re.compile(r'\bwill not\b', re.IGNORECASE): 'won\'t',
            re.compile(r'\bis not\b', re.IGNORECASE): 'isn\'t',
            re.compile(r'\bI believe\b', re.IGNORECASE): 'I think',
            re.compile(r'\bsomewhat\b', re.IGNORECASE): 'kinda',
            re.compile(r'\bhello\b', re.IGNORECASE): 'hey',
            re.compile(r'\byes\b', re.IGNORECASE): 'yeah'
        },
        'prefix': 'Hey there! ',
        'suffix': ' Hope this helps!'
    },
    'professional': {
        'replacements': {
            re.compile(r'\bcan\'t\b', re.IGNORECASE): 'cannot',
            re.compile(r'\bdon\'t\b', re.IGNORECASE): 'do not',
            re.compile(r'\bI think\b', re.IGNORECASE): 'In my professional opinion',
            re.compile(r'\bmaybe\b', re.IGNORECASE): 'perhaps',
            re.compile(r'\bstuff\b', re.IGNORECASE): 'materials',
            re.compile(r'\bfigure out\b', re.IGNORECASE): 'determine',
            re.compile(r'\bfind out\b', re.IGNORECASE): 'ascertain'
        },
        'prefix': 'Based on my analysis, ',
        'suffix': ' Please let me know if you require further clarification.'
    },
    'academic': {
        'replacements': {
            re.compile(r'\bcan\'t\b', re.IGNORECASE): 'cannot',
            re.compile(r'\bdon\'t\b', re.IGNORECASE): 'do not',
            re.compile(r'\bI think\b', re.IGNORECASE): 'This analysis suggests',
            re.compile(r'\bmaybe\b', re.IGNORECASE): 'it is plausible that',
            re.compile(r'\bstuff\b', re.IGNORECASE): 'factors',
            re.compile(r'\bfind out\b', re.IGNORECASE): 'determine',
            re.compile(r'\bshow\b', re.IGNORECASE): 'demonstrate'
        },
        'prefix': 'From an academic perspective, ',
        'suffix': ' This interpretation remains consistent with the available evidence.'
    },
    'friendly': {
        'replacements': {
            re.compile(r'\bHello\b', re.IGNORECASE): 'Hi there',
            re.compile(r'\bThank you\b', re.IGNORECASE): 'Thanks so much',
            re.compile(r'\bregards\b', re.IGNORECASE): 'best wishes',
            re.compile(r'\bsincerely\b', re.IGNORECASE): 'warmly'
        },
        'prefix': 'I\'m happy to share that ',
        'suffix': ' Looking forward to hearing from you!'
    },
    'persuasive': {
        'replacements': {
            re.compile(r'\bI think\b', re.IGNORECASE): 'I\'m confident that',
            re.compile(r'\bmaybe\b', re.IGNORECASE): 'certainly',
            re.compile(r'\bprobably\b', re.IGNORECASE): 'definitely',
            re.compile(r'\bcould\b', re.IGNORECASE): 'will',
            re.compile(r'\bmight\b', re.IGNORECASE): 'will undoubtedly'
        },
        'prefix': 'You\'ll find that ',
        'suffix': ' This opportunity shouldn\'t be missed!'
    }
}

def generate_tone_suggestions(text: str, tone: str) -> str:
    """Generate text suggestions based on tone."""

    if not text or not text.strip():
        return text

    tone_key = (tone or '').strip().lower()

    # Preferred path: Groq Cloud inference (centralized key)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_api_key,
            )
            prompt = (
                "You are an expert writing editor.\n"
                "Rewrite the text in the requested tone while preserving the exact meaning.\n"
                "Return only the rewritten text with no commentary.\n\n"
                f"Requested tone: {tone_key}\n"
                "Text:\n"
                f"\"\"\"{text}\"\"\""
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )
            rewritten = response.choices[0].message.content if response.choices else ""
            if rewritten:
                return rewritten.strip()
        except Exception as e:
            logger.warning(f"Groq tone generation failed for tone '{tone_key}': {e}")

    # Fallback path: deterministic regex-based transformations
    if tone_key not in TONE_TRANSFORMATIONS:
        return text

    transformed = text
    tone_config = TONE_TRANSFORMATIONS[tone_key]

    # Apply replacements using pre-compiled regex
    for pattern, replacement in tone_config['replacements'].items():
        transformed = pattern.sub(replacement, transformed)

    # Add prefix/suffix if text is short enough
    if len(transformed.split()) < 50:
        transformed = tone_config.get('prefix', '') + transformed + tone_config.get('suffix', '')

    return transformed