from flask import Blueprint, request, jsonify
from utils.llmresponder import get_response_from_gemini
from utils.apikey import require_api_key

query_bp = Blueprint("query", __name__)

DOCUMENT_CACHE = {} # maps hash(text) to an in-memory Chroma instance

@query_bp.route("/query", methods=["POST"])
# @require_api_key() # Disabled for local testing
def query_llm():
    data = request.get_json()
    user_query = data.get("query")
    context_text = data.get("context", "")

    if not user_query:
        return jsonify({"error": "Query missing."}), 400

    try:
        if not context_text:
            result = get_response_from_gemini("No document provided.", user_query)
            return jsonify({"response": result}), 200

        import hashlib
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from utils.chromavecdb import get_embed
        
        text_hash = hashlib.md5(context_text.encode('utf-8')).hexdigest()
        
        if text_hash not in DOCUMENT_CACHE:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_text(context_text)
            
            embeddings = get_embed()
            # Create in-memory Chroma vectorstore without saving to disk
            db = Chroma.from_texts(texts=chunks, embedding=embeddings)
            DOCUMENT_CACHE[text_hash] = db
            
        db = DOCUMENT_CACHE[text_hash]
        results = db.similarity_search(user_query, k=5)
        
        if not results:
            rag_context = context_text[:2000]
        else:
            rag_context = "\n\n----\n\n".join([doc.page_content for doc in results])
            
        result = get_response_from_gemini(rag_context, user_query)
            
        return jsonify({"response": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
