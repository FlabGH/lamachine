from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lamachine:lamachine@postgres:5432/lamachine",
)


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
