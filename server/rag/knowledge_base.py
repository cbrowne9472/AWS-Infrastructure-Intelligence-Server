from server.rag.ingestor import ingest_document
from server.rag.retriever import search_knowledge_base


def search_runbooks(query: str, doc_type: str = None) -> dict:
    results = search_knowledge_base(query, doc_type=doc_type)
    return {
        "query": query,
        "results_count": len(results),
        "results": results,
    }


def add_document(content: str, title: str, doc_type: str) -> dict:
    return ingest_document(content, title, doc_type)
