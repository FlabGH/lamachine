from app.api.documentary import (
    LEXICAL_SEARCH_TEXT_SQL,
    _build_lexical_websearch_query,
    _significant_lexical_terms,
)


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
