from app.db import normalize_psycopg_url


def test_normalize_psycopg_url_accepts_sqlalchemy_psycopg_scheme():
    assert (
        normalize_psycopg_url("postgresql+psycopg://user:pass@postgres:5432/db")
        == "postgresql://user:pass@postgres:5432/db"
    )


def test_normalize_psycopg_url_keeps_plain_postgresql_scheme():
    assert (
        normalize_psycopg_url("postgresql://user:pass@postgres:5432/db")
        == "postgresql://user:pass@postgres:5432/db"
    )
