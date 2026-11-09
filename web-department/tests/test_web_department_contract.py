import ast
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
    assert "REMOTEPAY_MODE: live" in (ROOT / "docker-compose.production.yml").read_text()
    assert "Payment is not verified as paid" in api


def test_internal_apps_do_not_hardcode_localhost_api():
    for name in ("dashboard/index.html", "rider/index.html", "signup/index.html", "track/index.html"):
        text = (ROOT / "static" / name).read_text()
        assert "127.0.0.1:8100" not in text
        assert "window.UBERNIE_WEB_DEPARTMENT_API" in text


def test_production_container_contract_exists():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.production.yml").exists()
    assert (ROOT / "PRODUCTION.md").exists()


def test_mock_checkout_routes_are_blocked_in_production():
    source = (ROOT / "api.py").read_text()
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    guard = functions["_block_mock_checkout_in_production"]
    checks_production = any(
        isinstance(node, ast.Compare)
        and any(isinstance(child, ast.Constant) and child.value == "production" for child in ast.walk(node))
        for node in ast.walk(guard)
    )
    returns_not_found = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "HTTPException"
        and any(
            keyword.arg == "status_code"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == 404
            for keyword in node.keywords
        )
        for node in ast.walk(guard)
    )
    assert checks_production
    assert returns_not_found

    for route_name in (
        "mock_checkout_page",
        "mock_checkout_pay",
        "mock_checkout_cancel",
        "mock_return",
    ):
        route = functions[route_name]
        calls_guard = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_block_mock_checkout_in_production"
            for node in ast.walk(route)
        )
        assert calls_guard, f"{route_name} must block mock checkout in production"
