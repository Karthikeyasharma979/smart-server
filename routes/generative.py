from flask import Blueprint, request, jsonify

from utils.GenerativeAI import chat
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_MODELS = {
    "cohere/Cohere-command-r-plus-08-2024",
    "openai/gpt-4o-mini",
    "meta/Llama-3.3-70B-Instruct",
    # Backward compatibility with existing frontend model ids.
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
}

generative_bp = Blueprint("generative", __name__)

@generative_bp.route("/generative", methods=["POST"])
def generative():
    try:
        data = request.get_json(silent=True) or {}
        
        if not data or 'user' not in data or 'text' not in data:
            return jsonify({"error": "User and text are required"}), 400
        
        text = str(data['text']).strip()
        tone = str(data.get('tone', 'neutral')).strip().lower()
        user = str(data['user']).strip()
        requested_model = str(data.get('model', 'cohere/Cohere-command-r-plus-08-2024')).strip()
        model = requested_model if requested_model in SUPPORTED_MODELS else "cohere/Cohere-command-r-plus-08-2024"
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if len(text) > 10000:  # Limit text length
            return jsonify({"error": "Text too long (max 10000 characters)"}), 400
        
        logger.info(f"Processing text for user: {user}, length: {len(text)}, model: {model}")
        
        request_source = str(data.get('source', '')).strip().lower()
        use_github_fallback = request_source == 'ai_chat'

        output = chat(text, tone, model, use_github_fallback=use_github_fallback)

        response={
            "output":output
        }
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in posttext: {e}")
        return jsonify({"error": "AI service temporarily unavailable. Please try again shortly."}), 503
