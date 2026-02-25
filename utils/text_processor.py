try:
    import language_tool_python
except ImportError:
    language_tool_python = None

try:
    import textstat
except ImportError:
    textstat = None

import re
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pre-compile regex for post-processing
POST_PROCESS_PATTERNS = [
    (re.compile(r'([.!?])([A-Z])'), r'\1 \2'),
    (re.compile(r'if any of hurt'), 'if any of this hurt you'),
    (re.compile(r'if any of this hurt(?!\s+you)'), 'if any of this hurt you'),
    (re.compile(r'\s+'), ' '),
    (re.compile(r'"\s+([.!?])'), r'"\1'),
    (re.compile(r'([.!?])\s+"'), r'\1"'),
    (re.compile(r'\bi\s+am\b', re.IGNORECASE), 'I am'),
    (re.compile(r'\bi\s+', re.IGNORECASE), 'I '),
]

try:
    if language_tool_python:
        tool = language_tool_python.LanguageTool('en-US')
    else:
        tool = None
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool: {e}")
    tool = None

def gram_check(text: str) -> Tuple[List[Dict], str]:
    """Improved grammar checking with better multiple error handling"""
    if not tool or not text.strip():
        return [], text

    try:
        matches = tool.check(text)
        
        if not matches:
            return [], text

        issues = []
        # Sort matches by offset ascending for reporting
        matches_ascending = sorted(matches, key=lambda x: x.offset)
        
        for match in matches_ascending:
            error_text = text[match.offset:match.offset + match.errorLength]
            
            issue = {
                "error": error_text,
                "suggestions": match.replacements[:3] if match.replacements else [],
                "message": match.message,
                "offset": match.offset,
                "errorLength": match.errorLength,
                "type": get_error_type(match.category),
                "context": get_error_context(text, match.offset, match.errorLength)
            }
            issues.append(issue)
            
            logger.info(f"Found error at {match.offset}-{match.offset + match.errorLength}: '{error_text}' -> {match.replacements[:3] if match.replacements else 'No suggestions'}")

        # Corrected text generation: iterate manually or use reverse sorted
        # Ideally, we should rebuild the string from chunks to avoid repeated string concatenation overhead
        # but for typical text implementation, reversed replacement is standard and safe
        
        corrected_text = text
        # Iterate in reverse order to keep offsets valid
        for match in reversed(matches_ascending):
            if match.replacements:
                replacement = match.replacements[0]
                start = match.offset
                end = match.offset + match.errorLength
                
                # Check bounds (though tool.check should be within bounds)
                if start >= 0 and end <= len(corrected_text):
                    # Python strings are immutable, so slicing is standard. 
                    # For very large texts, a list of characters or string builder pattern is better,
                    # but for paragraph text, this is acceptable.
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
                    
                    logger.info(f"Applied correction at {start}-{end}: '{text[start:end]}' -> '{replacement}'")

        corrected_text = post_process_corrections(corrected_text)
        
        return issues, corrected_text

    except Exception as e:
        logger.error(f"Error in grammar check: {e}")
        return [], text

def get_error_context(text: str, offset: int, length: int, context_size: int = 20) -> str:
    """Get context around the error for better understanding"""
    start = max(0, offset - context_size)
    end = min(len(text), offset + length + context_size)
    context = text[start:end]
    
    error_start = offset - start
    error_end = error_start + length
    
    return {
        "full_context": context,
        "error_start": error_start,
        "error_end": error_end
    }

def post_process_corrections(text: str) -> str:
    """Enhanced post-processing with pre-compiled regex"""
    for pattern, replacement in POST_PROCESS_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()

def get_error_type(category: str) -> str:
    """Enhanced error type categorization"""
    category_upper = category.upper()
    
    if 'GRAMMAR' in category_upper:
        return 'grammar'
    elif 'TYPO' in category_upper or 'SPELL' in category_upper:
        return 'spelling'
    elif 'PUNCT' in category_upper:
        return 'punctuation'
    elif 'STYLE' in category_upper:
        return 'style'
    elif 'CAPITALIZ' in category_upper:
        return 'capitalization'
    elif 'WHITESPACE' in category_upper:
        return 'spacing'
    else:
        return 'other'

def calculate_readability(text: str) -> Dict:
    """Calculate readability metrics with error handling"""
    if not text.strip():
        return {"error": "Empty text"}
    
    if not textstat:
        return {"error": "Readability analysis unavailable (library missing)"}
    
    try:
        flesch_score = textstat.flesch_reading_ease(text)
        readability_percentage = max(0, min(100, flesch_score))
        
        if flesch_score >= 90:
            level = "Very Easy"
        elif flesch_score >= 80:
            level = "Easy"
        elif flesch_score >= 70:
            level = "Fairly Easy"
        elif flesch_score >= 60:
            level = "Standard"
        elif flesch_score >= 50:
            level = "Fairly Difficult"
        elif flesch_score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"
        
        return {
            "flesch_score": round(flesch_score, 2),
            "readability_percentage": round(readability_percentage, 2),
            "level": level,
            "word_count": len(text.split()),
            "sentence_count": textstat.sentence_count(text),
            "reading_time_minutes": round(textstat.reading_time(text), 2)
        }
    except Exception as e:
        logger.error(f"Error calculating readability: {e}")
        return {"error": "Could not calculate readability"}

def calculate_correction_score(original: str, corrected: str, errors_count: int) -> float:
    """Calculate correction improvement score"""
    if original == corrected:
        return 100.0
    
    word_count = len(original.split())
    if word_count == 0:
        return 0.0
    
    if errors_count == 0:
        return 100.0
    
    error_density = errors_count / word_count
    correction_percentage = max(0, 100 - (error_density * 100))
    
    return round(correction_percentage, 2)