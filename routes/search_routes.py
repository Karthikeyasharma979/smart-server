from flask import Blueprint, request, jsonify
from ddgs import DDGS
import logging

# Configure logger
logger = logging.getLogger(__name__)

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/search', methods=['POST'])
def web_search():
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'success': False, 'error': 'Query parameter is required'}), 400
        
        query = data.get('query')
        num_results = data.get('max_results', 5)

        logger.info(f"Performing DuckDuckGo search for: {query}")
        
        results = []
        # ddgs = DDGS()
        # Fetch search results
        with DDGS() as ddgs:
            # We use ddgs.text for regular web text results
            ddg_results = ddgs.text(query, max_results=num_results)
            for r in ddg_results:
                results.append({
                    'title': r.get('title'),
                    'body': r.get('body'),
                    'href': r.get('href')
                })
        
        return jsonify({'success': True, 'results': results}), 200

    except Exception as e:
        logger.error(f"Error during DuckDuckGo search: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
