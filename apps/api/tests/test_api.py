import os
import pytest

os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-dummy")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_transactions_list():
    r = client.get("/transactions/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_reports_trial_balance():
    r = client.get("/reports/trial-balance")
    assert r.status_code == 200


def test_reports_dashboard_summary():
    r = client.get("/reports/dashboard-summary")
    assert r.status_code == 200
    data = r.json()
    assert "revenue_cents" in data
    assert "expenses_cents" in data
    assert "auto_cat_rate" in data


def test_reports_profit_loss():
    r = client.get("/reports/profit-loss")
    assert r.status_code == 200


def test_accounts_list():
    r = client.get("/accounts/")
    assert r.status_code == 200
