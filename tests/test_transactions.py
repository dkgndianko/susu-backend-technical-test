from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.db.in_memory_database import InMemoryDB


client = TestClient(main.app)


@pytest.fixture
def deposit_transaction():
    return {
        "amount": 10.5,
        "type": "deposit",
        "date": date.today().strftime("%Y-%m-%d"),
    }


@pytest.fixture
def mock_database(monkeypatch):
    test_json_data = "tests/tables_test.json"
    mocked_db = InMemoryDB(test_json_data)
    monkeypatch.setattr(main, "db", mocked_db)

def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_transactions():
    response = client.get("users/1/transactions")
    assert response.status_code == 200
    for transaction in response.json():
        assert transaction["user_id"] == 1


def test_get_existing_transaction():
    response = client.get("users/1/transactions/1")
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["user_id"] == 1
    assert transaction["id"] == 1


def test_get_nonexisting_transaction():
    response = client.get("users/1/transactions/9999")
    assert response.status_code == 404


def test_get_transaction_nonexisting_user():
    response = client.get("users/999/transactions/1")
    assert response.status_code == 404


def test_create_transaction(deposit_transaction):
    response = client.post("users/2/transactions", json=deposit_transaction)
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["user_id"] == 2
    assert transaction["amount"] == 10.5
    assert transaction["type"] == "deposit"
    assert transaction["date"] == date.today().isoformat()
    assert transaction["state"] == "pending"


def test_get_balance_for_non_exising_user(mock_database):
    response = client.get("users/10/transactions/balance")
    assert response.status_code == 404


def test_get_balance_when_no_transactions(mock_database):
    response = client.get("users/4/transactions/balance")
    assert response.status_code == 200
    data = response.json()
    withdrawals = data["withdrawals"]
    balance = data["balance"]
    assert withdrawals == []
    assert balance == 0

def test_get_balance_total_coverage(mock_database):
    response = client.get("users/5/transactions/balance")
    assert response.status_code == 200
    data = response.json()
    withdrawals = data["withdrawals"]
    balance = data["balance"]
    assert len(withdrawals) == 1
    assert balance == 0

def test_get_balance_unsufficient_funds(mock_database):
    response = client.get("users/6/transactions/balance")
    assert response.status_code == 200
    data = response.json()
    withdrawals = data["withdrawals"]
    balance = data["balance"]
    assert len(withdrawals) == 3
    assert balance == 0
    last_withdrawal = withdrawals[-1]
    assert last_withdrawal["amount"] == 10
    assert last_withdrawal["covered_amount"] == 0
    assert last_withdrawal["covered_rate"] == 0

def test_get_balance_partial_coverage(mock_database):
    response = client.get("users/7/transactions/balance")
    assert response.status_code == 200
    data = response.json()
    withdrawals = data["withdrawals"]
    balance = data["balance"]
    assert len(withdrawals) == 3
    assert balance == 0
    last_withdrawal = withdrawals[-1]
    assert last_withdrawal["amount"] == 15
    assert last_withdrawal["covered_amount"] == 10
    assert last_withdrawal["covered_rate"] == 66.67


def test_balance_sufficient_funds(mock_database):
    response = client.get("users/8/transactions/balance")
    assert response.status_code == 200
    data = response.json()
    withdrawals = data["withdrawals"]
    balance = data["balance"]
    assert len(withdrawals) == 7
    assert balance == 40
    last_withdrawal = withdrawals[-1]
    assert last_withdrawal["amount"] == 10
    assert last_withdrawal["covered_amount"] == 10
    assert last_withdrawal["covered_rate"] == 100