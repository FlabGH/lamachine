from app.api.documentary import (
    LEXICAL_SEARCH_TEXT_SQL,
    GenerateNoteRequest,
    SearchRequest,
    _build_lexical_websearch_query,
    _significant_lexical_terms,
)


INDEX_VERSION_ID = "00000000-0000-0000-0000-000000000000"


def test_significant_lexical_terms_filters_short_words_and_stopwords():
    terms = _significant_lexical_terms(
        "Quelle est la position de LFI sur la souveraineté numérique ?"
    )

    assert terms == ["position", "lfi", "souveraineté", "numérique"]


def test_build_lexical_websearch_query_uses_or_terms_for_tolerant_recall():
    lexical_query = _build_lexical_websearch_query(
        "Quels retards la France accuse-t-elle dans la transformation de l’action publique par l’IA ?"
    )

    assert lexical_query == (
        "retards OR france OR accuse OR transformation OR action OR publique"
    )


def test_build_lexical_websearch_query_returns_none_without_significant_term():
    assert _build_lexical_websearch_query("le de à ou ?") is None


def test_lexical_search_text_includes_documentary_metadata_fields():
    assert "content" in LEXICAL_SEARCH_TEXT_SQL
    assert "source_code" in LEXICAL_SEARCH_TEXT_SQL
    assert "document_title" in LEXICAL_SEARCH_TEXT_SQL
    assert "role_documentaire" in LEXICAL_SEARCH_TEXT_SQL
    assert "theme_tags" in LEXICAL_SEARCH_TEXT_SQL


def test_search_request_uses_poc_retrieval_defaults(monkeypatch):
    monkeypatch.delenv("DOCUMENTARY_SEARCH_TOP_K", raising=False)
    monkeypatch.delenv("DOCUMENTARY_RERANK_TOP_K", raising=False)

    request = SearchRequest(query="test", index_version_id=INDEX_VERSION_ID)

    assert request.top_k == 30
    assert request.rerank_top_k == 20


def test_search_request_defaults_are_configurable_from_env(monkeypatch):
    monkeypatch.setenv("DOCUMENTARY_SEARCH_TOP_K", "12")
    monkeypatch.setenv("DOCUMENTARY_RERANK_TOP_K", "7")

    request = SearchRequest(query="test", index_version_id=INDEX_VERSION_ID)

    assert request.top_k == 12
    assert request.rerank_top_k == 7


def test_generate_note_request_uses_same_retrieval_defaults(monkeypatch):
    monkeypatch.setenv("DOCUMENTARY_SEARCH_TOP_K", "14")
    monkeypatch.setenv("DOCUMENTARY_RERANK_TOP_K", "8")

    request = GenerateNoteRequest(query="test", index_version_id=INDEX_VERSION_ID)

    assert request.top_k == 14
    assert request.rerank_top_k == 8
