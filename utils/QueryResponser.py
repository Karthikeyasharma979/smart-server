from utils.chromavecdb import get_embed 
from utils.llmresponder import get_response_from_gemini

CHROMA_PATH = "./chroma_db" 

def response(query_text):
    from langchain_chroma import Chroma  # Lazy import
    if not query_text:
        return []

    embeddings = get_embed()

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    results = db.similarity_search(query_text, k=5)

    if not results:
        return []
    else:
        context = "\n\n----\n\n".join([doc.page_content for doc in results])
        return get_response_from_gemini(context, query_text)


