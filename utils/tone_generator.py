import re
import logging

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
    """Generate text suggestions based on tone"""
    
    if tone not in TONE_TRANSFORMATIONS:
        return text
    
    transformed = text
    tone_config = TONE_TRANSFORMATIONS[tone]
    
    # Apply replacements using pre-compiled regex
    for pattern, replacement in tone_config['replacements'].items():
        transformed = pattern.sub(replacement, transformed)
    
    # Add prefix/suffix if text is short enough
    if len(transformed.split()) < 50:
        transformed = tone_config.get('prefix', '') + transformed + tone_config.get('suffix', '')
    
    return transformed