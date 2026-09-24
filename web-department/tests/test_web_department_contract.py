from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_cover_imports():
    req = (ROOT / "requirements.txt").read_text()
    for package in ("bcrypt", "python-jose", "psycopg", "pytest"):
        assert package in req


def test_production_contract_disables_mock_fallback():
    api = (ROOT / "api.py").read_text()
    env = (ROOT / ".env.example").read_text()
    assert "REMOTEPAY_MODE" in api
    assert "REMOTEPAY_WEBHOOK_SECRET" in api
    assert "REMOTEPAY_MODE=live" in env
    assert "payment is not verified as paid" in api


def test_internal_apps_do_not_hardcode_localhost_api():
    for name in ("dashboard/index.html", "rider/index.html", "signup/index.html", "track/index.html"):
        text = (ROOT / "static" / name).read_text()
        assert "127.0.0.1:8100" not in text
        assert "window.UBERNIE_WEB_DEPARTMENT_API" in text


def test_production_container_contract_exists():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.production.yml").exists()
    assert (ROOT / "PRODUCTION.md").exists()
