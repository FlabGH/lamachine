from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DB_DIR = REPO_ROOT / "apps" / "api" / "app" / "db"
INITIAL_SCHEMA = DB_DIR / "migrations" / "001_documentary_schema.sql"
STRUCTURED_OBJECTS_MIGRATION = DB_DIR / "migrations" / "003_structured_objects.sql"
FIXTURE = DB_DIR / "fixtures" / "sample_documentary_fixture.sql"
AUDIT_QUERIES = DB_DIR / "queries" / "audit_documentary_metadata.sql"
DESTRUCTIVE_SQL = ("DROP ", "TRUNCATE ", "DELETE ")


def test_documentary_metadata_sql_files_exist():
    assert INITIAL_SCHEMA.is_file()
    assert STRUCTURED_OBJECTS_MIGRATION.is_file()
    assert FIXTURE.is_file()
    assert AUDIT_QUERIES.is_file()


def test_initial_schema_uses_canonical_core_tables():
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8")

    assert "CREATE TABLE sources" in sql
    assert "code TEXT NOT NULL" in sql
    assert "CREATE TABLE documents" in sql
    assert "CREATE TABLE document_chunks" in sql
    assert "CREATE TABLE outputs" not in sql
    assert "CREATE TABLE output_sources" not in sql
    assert "name TEXT NOT NULL" not in sql.split("CREATE TABLE documents", 1)[0]


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


def test_sample_fixture_contains_canonical_document_metadata():
    sql = FIXTURE.read_text(encoding="utf-8")

    assert "Sample document" in sql
    assert '"source_code": "sample"' in sql
    assert '"theme_tags": ["sample"]' in sql


def test_documentary_metadata_audit_queries_are_read_only():
    sql = AUDIT_QUERIES.read_text(encoding="utf-8").upper()

    assert "SELECT" in sql
    assert "DOCUMENT_CHUNKS" in sql
    assert not any(statement in sql for statement in DESTRUCTIVE_SQL)
