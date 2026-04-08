from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from utils.text_processor import gram_check, calculate_readability, calculate_correction_score
from utils.tone_generator import generate_tone_suggestions

logger = logging.getLogger(__name__)

text_bp = Blueprint('text_routes', __name__)

@text_bp.route('/posttext', methods=['POST'])
def posttext():
    """Process and analyze text"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        user = data.get('user', 'anonymous')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Grammar check and correction
        issues, corrected_text = gram_check(text)
        
        # Calculate readability metrics
        readability = calculate_readability(corrected_text)
        
        # Calculate correction score
        correction_score = calculate_correction_score(text, corrected_text, len(issues))
        
        # Generate tone variations
        tone_suggestions = {
            'formal': generate_tone_suggestions(corrected_text, 'formal'),
            'casual': generate_tone_suggestions(corrected_text, 'casual'),
            'professional': generate_tone_suggestions(corrected_text, 'professional'),
            'academic': generate_tone_suggestions(corrected_text, 'academic'),
            'friendly': generate_tone_suggestions(corrected_text, 'friendly'),
            'persuasive': generate_tone_suggestions(corrected_text, 'persuasive')
        }
        
        # Prepare response
        result = {
            "original_text": text,
            "corrected_text": corrected_text,
            "errors": issues,
            "correction_score": correction_score,
            "readability": readability,
            "tone_suggestions": tone_suggestions,
            "timestamp": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "user": user
        }
        
        return jsonify({"success": True, "results": [result]}), 200
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500



@text_bp.route('/tones', methods=['GET'])
def get_available_tones():
    """Get list of available tone transformations"""
    tones = ['formal', 'casual', 'professional', 'academic', 'friendly', 'persuasive']
    return jsonify({"tones": tones}), 200