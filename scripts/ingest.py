import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.rag.ingestor import ingest_file


def ingest_directory(directory: str, doc_type: str):
    files = [f for f in os.listdir(directory) if f.endswith(".md")]
    print(f"Ingesting {len(files)} files from {directory} as {doc_type}...")
    for filename in files:
        path = os.path.join(directory, filename)
        result = ingest_file(path, doc_type)
        print(f"  + {result['title']} ({result['chunks_created']} chunks)")


if __name__ == "__main__":
    ingest_directory("knowledge_base/runbooks", "runbook")
    ingest_directory("knowledge_base/incidents", "incident")
    ingest_directory("knowledge_base/architecture", "architecture")
    print("\nIngestion complete.")
