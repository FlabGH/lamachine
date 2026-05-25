from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DB_DIR = REPO_ROOT / "apps" / "api" / "app" / "db"
MIGRATION = DB_DIR / "migrations" / "002_documentary_metadata_contract.sql"
FIXTURE = DB_DIR / "fixtures" / "phase3_step1_fixture.sql"
AUDIT_QUERIES = DB_DIR / "queries" / "audit_documentary_metadata.sql"
DESTRUCTIVE_SQL = ("DROP ", "TRUNCATE ", "DELETE ")


def test_documentary_metadata_sql_files_exist():
    assert MIGRATION.is_file()
    assert FIXTURE.is_file()
    assert AUDIT_QUERIES.is_file()


def test_documentary_metadata_migration_stays_jsonb_only():
    sql = MIGRATION.read_text(encoding="utf-8").upper()

    assert "CREATE INDEX IF NOT EXISTS" in sql
    assert "METADATA->>" in sql
    assert "ALTER TABLE" not in sql
    assert not any(statement in sql for statement in DESTRUCTIVE_SQL)


def test_documentary_metadata_fixture_contains_minimal_contract_keys():
    sql = FIXTURE.read_text(encoding="utf-8")

    for key in (
        "source_id",
        "document_id",
        "document_title",
        "source_name",
        "content_sha256",
        "index_version_id",
        "vector_collection",
    ):
        assert f'"{key}"' in sql


def test_documentary_metadata_audit_queries_are_read_only():
    sql = AUDIT_QUERIES.read_text(encoding="utf-8").upper()

    assert "SELECT" in sql
    assert "DOCUMENT_CHUNKS" in sql
    assert not any(statement in sql for statement in DESTRUCTIVE_SQL)
