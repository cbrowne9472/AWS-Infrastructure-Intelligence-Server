from unittest.mock import MagicMock, patch

from server.rag import knowledge_base


def test_search_runbooks_formats_response():
    mock_results = [
        {
            "content": "Lambda timeout runbook content",
            "title": "lambda-timeout",
            "doc_type": "runbook",
            "relevance_score": 0.92,
        }
    ]

    with patch("server.rag.knowledge_base.search_knowledge_base", return_value=mock_results):
        result = knowledge_base.search_runbooks("Lambda timeout")

    assert result["query"] == "Lambda timeout"
    assert result["results_count"] == 1
    assert result["results"][0]["title"] == "lambda-timeout"
    assert result["results"][0]["relevance_score"] == 0.92


def test_search_runbooks_passes_doc_type_filter():
    with patch("server.rag.knowledge_base.search_knowledge_base", return_value=[]) as mock_search:
        knowledge_base.search_runbooks("RDS high CPU", doc_type="runbook")

    mock_search.assert_called_once_with("RDS high CPU", doc_type="runbook")


def test_search_runbooks_empty_results():
    with patch("server.rag.knowledge_base.search_knowledge_base", return_value=[]):
        result = knowledge_base.search_runbooks("something obscure")

    assert result["results_count"] == 0
    assert result["results"] == []


def test_ingest_document_chunks_and_upserts():
    mock_index = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.1] * 1536

    with (
        patch("server.rag.ingestor.Pinecone") as mock_pinecone_cls,
        patch("server.rag.ingestor.embeddings", mock_embeddings),
    ):
        mock_pinecone_cls.return_value.Index.return_value = mock_index

        from server.rag.ingestor import ingest_document

        result = ingest_document(
            "## Section One\n\nSome content here.\n\n## Section Two\n\nMore content.",
            title="test-runbook",
            doc_type="runbook",
        )

    assert result["title"] == "test-runbook"
    assert result["doc_type"] == "runbook"
    assert result["chunks_created"] > 0
    assert result["status"] == "ingested"
    mock_index.upsert.assert_called_once()


def test_ingest_document_upsert_payload_shape():
    mock_index = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.0] * 1536

    with (
        patch("server.rag.ingestor.Pinecone") as mock_pinecone_cls,
        patch("server.rag.ingestor.embeddings", mock_embeddings),
    ):
        mock_pinecone_cls.return_value.Index.return_value = mock_index

        from server.rag.ingestor import ingest_document

        ingest_document("Short content.", title="arch-doc", doc_type="architecture")

    call_args = mock_index.upsert.call_args
    vectors = call_args.kwargs.get("vectors") or call_args.args[0]
    assert len(vectors) >= 1
    v = vectors[0]
    assert "id" in v
    assert "values" in v
    assert v["metadata"]["title"] == "arch-doc"
    assert v["metadata"]["doc_type"] == "architecture"
