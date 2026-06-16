import os

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from server.config import settings

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.openai_api_key,
)


def search_knowledge_base(query: str, doc_type: str = None, top_k: int = None) -> list[dict]:
    """
    Semantic search over the knowledge base.
    Optionally filter by doc_type: runbook | incident | architecture
    """
    k = top_k or settings.rag_top_k

    vector_store = PineconeVectorStore(
        index_name=settings.pinecone_index_name,
        embedding=embeddings,
        pinecone_api_key=settings.pinecone_api_key,
    )

    filter_dict = {}
    if doc_type:
        filter_dict["doc_type"] = {"$eq": doc_type}

    results = vector_store.similarity_search_with_score(
        query,
        k=k,
        filter=filter_dict if filter_dict else None,
    )

    return [
        {
            "content": doc.page_content,
            "title": doc.metadata.get("title"),
            "doc_type": doc.metadata.get("doc_type"),
            "relevance_score": round(float(score), 4),
        }
        for doc, score in results
    ]
