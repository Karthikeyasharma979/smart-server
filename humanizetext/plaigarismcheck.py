from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
import logging
from utils.Comparator import compare_texts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

check_bp = Blueprint("check", __name__)

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

def check_plagiarism(text: str):
    client = get_client()
    prompt = (
        f"You are an expert AI-detection and plagiarism analysis system. Your task is to thoroughly analyze the provided text and determine its originality.\n\n"
        f"Guidelines:\n"
        f"- Estimate the percentage of the text that appears to be AI-generated versus human-written.\n"
        f"- Estimate the percentage of the text that appears to be copied from common internet sources without proper attribution.\n"
        f"- Provide a concise, clear explanation detailing the reasoning behind your analysis, pointing out specific patterns (e.g., repetitive phrasing, lack of burstiness, or typical AI clichés) if applicable.\n"
        f"- Format your response clearly using Markdown (e.g., use bullet points and bold text for key metrics).\n\n"
        f"Text to Analyze:\n"
        f"\"\"\"{text}\"\"\""
    )

    try:
        completion = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in plagiarism check: {e}")
        raise e

@check_bp.route("/plagiarism", methods=["POST"])
def check_plag():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
            
        # Case 1: Text Comparison (two texts)
        text1 = data.get('text1')
        text2 = data.get('text2')
        
        if text1 and text2:
            logger.info("Performing dual-text comparison.")
            output = compare_texts(text1.strip(), text2.strip())
            return jsonify({"output": output, "mode": "comparison"}), 200
            
        # Case 2: Standard Plagiarism Check (one text)
        text = data.get('text')
        if not text:
            return jsonify({"error": "Missing text, text1, or text2 parameter"}), 400
        
        text = text.strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        logger.info(f"Performing single-text analysis: {text[:50]}...")
        output = check_plagiarism(text)
        return jsonify({"output": output, "mode": "analysis"}), 200
        
    except Exception as e:
        logger.error(f"Error in plagiarism route: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
