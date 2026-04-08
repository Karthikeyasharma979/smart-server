from flask import Blueprint, request, jsonify
from utils.llmresponder import get_response_from_docqa_model
from utils.apikey import require_api_key

query_bp = Blueprint("query", __name__)

DOCUMENT_CACHE = {} # maps hash(text) to an in-memory Chroma instance
NO_ANSWER_PHRASE = "I cannot find the answer to that question in the provided document."
NO_TEXT_PHRASE = "I could not extract readable text from the uploaded document. Please upload a text-based PDF/DOCX/TXT file."


def _is_summary_query(query_text: str) -> bool:
    q = query_text.lower()
    summary_markers = (
        "summarize",
        "summary",
        "summarise",
        "overview",
        "tldr",
        "tl;dr",
        "brief",
        "key points",
    )
    return any(marker in q for marker in summary_markers)


def _build_broad_context(context_text: str, max_chars: int = 12000) -> str:
    if len(context_text) <= max_chars:
        return context_text

    head_len = int(max_chars * 0.67)
    tail_len = max_chars - head_len
    head = context_text[:head_len]
    tail = context_text[-tail_len:]
    return f"{head}\n\n---- CONTEXT TRUNCATED ----\n\n{tail}"


def _is_no_answer(response_text: str) -> bool:
    return response_text.strip().lower() == NO_ANSWER_PHRASE.lower()


def _local_summary_fallback(context_text: str, max_sentences: int = 4) -> str:
    cleaned = " ".join(context_text.split())
    if not cleaned:
        return NO_TEXT_PHRASE

    sentences = []
    start = 0
    for i, ch in enumerate(cleaned):
        if ch in ".!?":
            sentence = cleaned[start:i + 1].strip()
            if sentence:
                sentences.append(sentence)
            start = i + 1
        if len(sentences) >= max_sentences:
            break

    if not sentences:
        sentences = [cleaned[:700].strip()]

    summary = " ".join(sentences[:max_sentences]).strip()
    return f"**Document Summary:**\n- {summary}"

@query_bp.route("/query", methods=["POST"])
# @require_api_key() # Disabled for local testing
def query_llm():
    data = request.get_json(silent=True) or {}
    user_query = data.get("query")
    context_text = data.get("context", "")

    if not isinstance(user_query, str):
        user_query = str(user_query or "")

    if not isinstance(context_text, str):
        context_text = str(context_text)

    if not user_query:
        return jsonify({"error": "Query missing."}), 400

    try:
        if not context_text.strip():
            result = NO_TEXT_PHRASE
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
            
        if _is_summary_query(user_query):
            # Summary requests need wider context than narrow top-k retrieval.
            rag_context = _build_broad_context(context_text, max_chars=14000)
        else:
            db = DOCUMENT_CACHE[text_hash]
            results = db.similarity_search(user_query, k=5)

            if not results:
                rag_context = context_text[:3000]
            else:
                rag_context = "\n\n----\n\n".join([doc.page_content for doc in results])
            
        result = get_response_from_docqa_model(rag_context, user_query)

        # If retrieval context was too narrow, retry once with broader document context.
        if _is_no_answer(result):
            retry_context = _build_broad_context(context_text, max_chars=14000)
            if retry_context != rag_context:
                result = get_response_from_docqa_model(retry_context, user_query)

        if _is_summary_query(user_query) and _is_no_answer(result):
            result = _local_summary_fallback(context_text)
            
        return jsonify({"response": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
