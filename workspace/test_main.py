import pytest
from fastapi.testclient import TestClient
import os
import sqlite3
from main import app, DB_NAME, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
    yield
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

def test_create_account():
    response = client.post("/accounts/", json={"name": "Test User"})
    assert response.status_code == 200
    assert "account_id" in response.json()

def test_deposit_withdraw():
    acc = client.post("/accounts/", json={"name": "Test User"}).json()["account_id"]
    
    # Deposit
    res = client.post(f"/accounts/{acc}/deposit", json={"amount": 1000.0})
    assert res.status_code == 200
    
    # Portfolio Check
    port = client.get(f"/accounts/{acc}/portfolio").json()
    assert port["cash_balance"] == 1000.0
    
    # Withdraw
    res = client.post(f"/accounts/{acc}/withdraw", json={"amount": 500.0})
    assert res.status_code == 200
    
    # Withdraw Insufficient
    res = client.post(f"/accounts/{acc}/withdraw", json={"amount": 1000.0})
    assert res.status_code == 400

def test_buy_sell():
    acc = client.post("/accounts/", json={"name": "Trader"}).json()["account_id"]
    client.post(f"/accounts/{acc}/deposit", json={"amount": 10000.0})
    
    # Buy
    res = client.post(f"/accounts/{acc}/buy", json={"symbol": "AAPL", "quantity": 10})
    assert res.status_code == 200
    
    # Check holdings
    port = client.get(f"/accounts/{acc}/portfolio").json()
    assert any(h["symbol"] == "AAPL" and h["quantity"] == 10 for h in port["holdings"])
    assert port["cash_balance"] == (10000.0 - 150.0 * 10)
    
    # Sell
    res = client.post(f"/accounts/{acc}/sell", json={"symbol": "AAPL", "quantity": 5})
    assert res.status_code == 200
    
    # Check updated holdings
    port = client.get(f"/accounts/{acc}/portfolio").json()
    assert any(h["symbol"] == "AAPL" and h["quantity"] == 5 for h in port["holdings"])
    
    # Insufficient funds to buy
    res = client.post(f"/accounts/{acc}/buy", json={"symbol": "GOOGL", "quantity": 100})
    assert res.status_code == 400
    
    # Insufficient shares to sell
    res = client.post(f"/accounts/{acc}/sell", json={"symbol": "AAPL", "quantity": 100})
    assert res.status_code == 400

def test_history():
    acc = client.post("/accounts/", json={"name": "History User"}).json()["account_id"]
    client.post(f"/accounts/{acc}/deposit", json={"amount": 5000.0})
    client.post(f"/accounts/{acc}/buy", json={"symbol": "TSLA", "quantity": 1})
    
    hist = client.get(f"/accounts/{acc}/history").json()
    assert len(hist) > 0
    assert hist[-1]["symbol"] == "TSLA"
    assert hist[-1]["type"] == "BUY"

