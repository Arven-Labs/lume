from fastapi.testclient import TestClient

from app.main import app

API_KEY_HEADER = {"X-API-Key": "test-key"}


def _client(monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    from app.config import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def _clear():
    from app.config import get_settings

    get_settings.cache_clear()


def test_tax_rules_requires_api_key(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/v1/tax-rules/br")
    _clear()

    assert response.status_code == 401


def test_tax_rules_br_returns_rules(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/v1/tax-rules/br", headers=API_KEY_HEADER)
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert body["jurisdiction"] == "BR"
    by_key = {}
    for rule in body["rules"]:
        by_key.setdefault(rule["key"], []).append(rule)
    assert by_key["common_rate"][0]["value"] == 0.15
    assert by_key["stock_exemption_monthly_sales"][0]["value"] == 20000.0


def test_tax_rules_keep_history_per_effective_date(monkeypatch):
    client = _client(monkeypatch)
    body = client.get("/v1/tax-rules/br", headers=API_KEY_HEADER).json()
    _clear()

    jcp = sorted(
        (r for r in body["rules"] if r["key"] == "jcp_irrf_rate"),
        key=lambda r: r["effective_from"],
    )
    assert [r["value"] for r in jcp] == [0.15, 0.175]
    assert jcp[1]["effective_from"] == "2026-01-01"


def test_tax_rules_have_unique_key_and_date():
    from app.services.tax_rules_service import TAX_RULES_BR

    pairs = [(r.key, r.effective_from) for r in TAX_RULES_BR]
    assert len(pairs) == len(set(pairs))
