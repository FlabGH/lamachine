from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DB_DIR = REPO_ROOT / "apps" / "api" / "app" / "db"
INITIAL_SCHEMA = DB_DIR / "migrations" / "001_documentary_schema.sql"
MIGRATION = DB_DIR / "migrations" / "002_documentary_metadata_contract.sql"
STRUCTURED_OBJECTS_MIGRATION = DB_DIR / "migrations" / "003_structured_objects.sql"
FIXTURE = DB_DIR / "fixtures" / "phase3_step1_fixture.sql"
AUDIT_QUERIES = DB_DIR / "queries" / "audit_documentary_metadata.sql"
DESTRUCTIVE_SQL = ("DROP ", "TRUNCATE ", "DELETE ")


def test_documentary_metadata_sql_files_exist():
    assert INITIAL_SCHEMA.is_file()
    assert MIGRATION.is_file()
    assert STRUCTURED_OBJECTS_MIGRATION.is_file()
    assert FIXTURE.is_file()
    assert AUDIT_QUERIES.is_file()


def test_initial_schema_uses_source_code_column():
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8")

    assert "CREATE TABLE sources" in sql
    assert "code TEXT NOT NULL" in sql
    assert "chunking_version TEXT NOT NULL" in sql
    assert "split_strategy TEXT NOT NULL" in sql
    assert "min_chunk_size INTEGER NOT NULL" in sql
    assert "max_chunk_size INTEGER NOT NULL" in sql
    assert "UNIQUE (index_version_id, content_sha256)" in sql
    assert "idx_chunks_content_sha256" in sql
    assert "name TEXT NOT NULL" not in sql.split("CREATE TABLE documents", 1)[0]


def test_documentary_metadata_migration_stays_jsonb_only():
    sql = MIGRATION.read_text(encoding="utf-8").upper()

    assert "CREATE INDEX IF NOT EXISTS" in sql
    assert "METADATA->>" in sql
    assert "ALTER TABLE" not in sql
    assert not any(statement in sql for statement in DESTRUCTIVE_SQL)


def test_structured_objects_migration_adds_separate_storage():
    sql = STRUCTURED_OBJECTS_MIGRATION.read_text(encoding="utf-8").upper()
    sql_without_fk_delete_clause = sql.replace("ON DELETE ", "ON_DELETE_")

    assert "CREATE TABLE IF NOT EXISTS STRUCTURED_OBJECTS" in sql
    assert "CREATE TABLE IF NOT EXISTS STRUCTURED_OBJECT_CHUNKS" in sql
    assert "REFERENCES DOCUMENTS(ID) ON DELETE CASCADE" in sql
    assert "REFERENCES DOCUMENT_CHUNKS(ID) ON DELETE CASCADE" in sql
    assert "OBJECT_TYPE TEXT NOT NULL" in sql
    assert "SOURCE_SPAN JSONB NOT NULL DEFAULT '{}'" in sql
    assert "PRODUCER JSONB NOT NULL DEFAULT '{}'" in sql
    assert "IDX_STRUCTURED_OBJECTS_DOCUMENT_ID" in sql
    assert "IDX_STRUCTURED_OBJECTS_OBJECT_TYPE" in sql
    assert "IDX_STRUCTURED_OBJECTS_METADATA" in sql
    assert not any(statement in sql_without_fk_delete_clause for statement in DESTRUCTIVE_SQL)


def test_documentary_metadata_fixture_contains_minimal_contract_keys():
    sql = FIXTURE.read_text(encoding="utf-8")

    for key in (
        "source_id",
        "document_id",
        "document_title",
        "source_code",
        "role_documentaire",
        "statut_metadonnees",
        "content_sha256",
        "content_hash",
        "index_version_id",
        "vector_collection",
        "chunking_version",
        "split_strategy",
        "parent_document_id",
    ):
        assert f'"{key}"' in sql


def test_documentary_metadata_audit_queries_are_read_only():
    sql = AUDIT_QUERIES.read_text(encoding="utf-8").upper()

    assert "SELECT" in sql
    assert "DOCUMENT_CHUNKS" in sql
    assert not any(statement in sql for statement in DESTRUCTIVE_SQL)


def test_documentary_metadata_audit_queries_include_enriched_contract_keys():
    sql = AUDIT_QUERIES.read_text(encoding="utf-8")

    assert "role_documentaire" in sql
    assert "statut_metadonnees" in sql
    assert "chunking_version" in sql
    assert "split_strategy" in sql
    assert "parent_document_id" in sql
    assert "content_hash" in sql
    assert "duplicate_document_hash_groups" in sql
    assert "duplicate_chunk_hash_groups" in sql
    assert "documents_without_data_tags" in sql
    assert "documents_without_service_family" in sql
    assert "documents_without_visibility_scope" in sql
    assert "documents_without_access_level" in sql
    assert "documents_without_language" in sql
    assert "documents_without_collected_at" in sql
    assert "chunks_without_data_tags" in sql
    assert "chunks_without_service_family" in sql
    assert "chunks_without_visibility_scope" in sql
    assert "chunks_without_access_level" in sql
    assert "chunks_without_language" in sql
    assert "chunks_without_collected_at" in sql
    assert "organization_scoped_documents_without_organization_id" in sql
    assert "organization_scoped_chunks_without_organization_id" in sql
