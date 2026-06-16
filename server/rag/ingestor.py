import uuid

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

from server.config import settings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.openai_api_key,
)


def ingest_document(content: str, title: str, doc_type: str) -> dict:
    """
    doc_type: runbook | incident | architecture
    Chunks the document and upserts to Pinecone with metadata.
    """
    # Initialized inside the function so import doesn't make network calls
    # with placeholder credentials before real creds are in .env.
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    chunks = splitter.split_text(content)
    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = embeddings.embed_query(chunk)
        vectors.append(
            {
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "title": title,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
        )

    index.upsert(vectors=vectors)

    return {
        "title": title,
        "doc_type": doc_type,
        "chunks_created": len(chunks),
        "status": "ingested",
    }


def ingest_file(file_path: str, doc_type: str) -> dict:
    with open(file_path, "r") as f:
        content = f.read()
    title = file_path.split("/")[-1].replace(".md", "")
    return ingest_document(content, title, doc_type)
