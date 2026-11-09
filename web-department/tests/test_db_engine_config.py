"""Regression tests for fail-closed production database configuration."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

WEB_DEPARTMENT = Path(__file__).resolve().parents[1]


def _import_engine(*, environment: str, database_url: str | None):
    child_env = os.environ.copy()
    child_env["ENVIRONMENT"] = environment
    child_env.pop("DATABASE_URL", None)
    if database_url is not None:
        child_env["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-c", "import db.engine"],
        cwd=WEB_DEPARTMENT,
        env=child_env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_production_requires_database_url():
    result = _import_engine(environment="production", database_url=None)
    assert result.returncode != 0
    assert "DATABASE_URL must be configured in production" in result.stderr


@pytest.mark.parametrize(
    "database_url",
    ["sqlite:///:memory:", "mysql://user:pass@localhost/db", "postgresql://user:pass@localhost/db", "postgresql+psycopg2://user:pass@localhost/db"],
)
def test_production_rejects_non_postgres_database_urls(database_url):
    result = _import_engine(environment="production", database_url=database_url)
    assert result.returncode != 0
    assert "Production DATABASE_URL must use postgresql+psycopg://" in result.stderr


def test_production_accepts_installed_psycopg_v3_driver():
    result = _import_engine(
        environment="production",
        database_url="postgresql+psycopg://user:pass@localhost/ubernie",
    )
    assert result.returncode == 0, result.stderr


def test_development_can_use_sqlite():
    result = _import_engine(environment="development", database_url="sqlite:///:memory:")
    assert result.returncode == 0, result.stderr
