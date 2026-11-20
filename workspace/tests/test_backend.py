import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db
from backend.database import Base
import os

# Use a specific file path for the test database to ensure it's cleaned up.
# This approach avoids potential conflicts with an in-memory db during file operations if pytest re-runs parts.
# The path is relative to the project root for consistency.
TEST_DATABASE_FILE = "./test_sql_app.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DATABASE_FILE}"

# Create a new engine for the test database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="session")
def session_fixture():
    # Ensure the test database file is clean before starting
    if os.path.exists(TEST_DATABASE_FILE):
        os.remove(TEST_DATABASE_FILE)
    
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after the test
        Base.metadata.drop_all(bind=engine)
        # Remove the test database file
        if os.path.exists(TEST_DATABASE_FILE):
            os.remove(TEST_DATABASE_FILE)


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear() # Clear overrides after test


def test_create_account(client):
    response = client.post("/accounts/", json={"initial_deposit": 1000.0})
    assert response.status_code == 201
    data = response.json()
    assert data["initial_deposit"] == 1000.0
    assert data["cash_balance"] == 1000.0
    assert "id" in data

    account_id = data["id"]
    # Check if initial deposit is recorded as a transaction
    transactions_response = client.get(f"/accounts/{account_id}/transactions/")
    assert transactions_response.status_code == 200
    transactions = transactions_response.json()
    assert len(transactions) == 1
    assert transactions[0]["type"] == "DEPOSIT"
    assert transactions[0]["amount"] == 1000.0


def test_get_account_details(client):
    # Create an account first
    create_response = client.post("/accounts/", json={"initial_deposit": 500.0})
    account_id = create_response.json()["id"]

    # Get account details
    get_response = client.get(f"/accounts/{account_id}/")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == account_id
    assert data["initial_deposit"] == 500.0
    assert data["cash_balance"] == 500.0

    # Get non-existent account
    non_existent_response = client.get("/accounts/9999/")
    assert non_existent_response.status_code == 404
    assert non_existent_response.json() == {"detail": "Account not found"}


def test_deposit_funds(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 1000.0})
    account_id = create_response.json()["id"]

    # Successful deposit
    deposit_response = client.post(f"/accounts/{account_id}/deposit/", json={"amount": 200.0})
    assert deposit_response.status_code == 200
    data = deposit_response.json()
    assert data["cash_balance"] == 1200.0

    # Check transaction history
    transactions_response = client.get(f"/accounts/{account_id}/transactions/")
    assert transactions_response.status_code == 200
    transactions = transactions_response.json()
    assert len(transactions) == 2 # Initial deposit + new deposit
    assert transactions[0]["type"] == "DEPOSIT" # Most recent first
    assert transactions[0]["amount"] == 200.0

    # Deposit non-positive amount
    bad_deposit_response = client.post(f"/accounts/{account_id}/deposit/", json={"amount": 0.0})
    assert bad_deposit_response.status_code == 400
    assert bad_deposit_response.json() == {"detail": "Unable to deposit funds. Check amount."}

    bad_deposit_response = client.post(f"/accounts/{account_id}/deposit/", json={"amount": -50.0})
    assert bad_deposit_response.status_code == 400
    assert bad_deposit_response.json() == {"detail": "Unable to deposit funds. Check amount."}

    # Deposit to non-existent account
    non_existent_deposit = client.post("/accounts/9999/deposit/", json={"amount": 100.0})
    assert non_existent_deposit.status_code == 400
    assert non_existent_deposit.json() == {"detail": "Unable to deposit funds. Check amount."}


def test_withdraw_funds(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 1000.0})
    account_id = create_response.json()["id"]

    # Successful withdrawal
    withdraw_response = client.post(f"/accounts/{account_id}/withdraw/", json={"amount": 300.0})
    assert withdraw_response.status_code == 200
    data = withdraw_response.json()
    assert data["cash_balance"] == 700.0

    # Check transaction history
    transactions_response = client.get(f"/accounts/{account_id}/transactions/")
    assert transactions_response.status_code == 200
    transactions = transactions_response.json()
    assert len(transactions) == 2
    assert transactions[0]["type"] == "WITHDRAWAL"
    assert transactions[0]["amount"] == 300.0

    # Withdraw more than available cash
    insufficient_funds_response = client.post(f"/accounts/{account_id}/withdraw/", json={"amount": 1000.0})
    assert insufficient_funds_response.status_code == 400
    assert insufficient_funds_response.json() == {"detail": "Unable to withdraw funds. Insufficient cash or invalid amount."}
    
    # Check balance didn't change
    account_after_fail = client.get(f"/accounts/{account_id}/").json()
    assert account_after_fail["cash_balance"] == 700.0

    # Withdraw non-positive amount
    bad_withdraw_response = client.post(f"/accounts/{account_id}/withdraw/", json={"amount": 0.0})
    assert bad_withdraw_response.status_code == 400
    assert bad_withdraw_response.json() == {"detail": "Unable to withdraw funds. Insufficient cash or invalid amount."}

    bad_withdraw_response = client.post(f"/accounts/{account_id}/withdraw/", json={"amount": -50.0})
    assert bad_withdraw_response.status_code == 400
    assert bad_withdraw_response.json() == {"detail": "Unable to withdraw funds. Insufficient cash or invalid amount."}

    # Withdraw from non-existent account
    non_existent_withdraw = client.post("/accounts/9999/withdraw/", json={"amount": 100.0})
    assert non_existent_withdraw.status_code == 400
    assert non_existent_withdraw.json() == {"detail": "Unable to withdraw funds. Insufficient cash or invalid amount."}


def test_buy_stock(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 2000.0})
    account_id = create_response.json()["id"]

    # Buy AAPL (price 150.00)
    buy_aapl_response = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 5.0})
    assert buy_aapl_response.status_code == 200
    buy_data = buy_aapl_response.json()
    assert buy_data["type"] == "BUY"
    assert buy_data["symbol"] == "AAPL"
    assert buy_data["quantity"] == 5.0
    assert buy_data["price"] == 150.0
    assert buy_data["amount"] == 750.0

    # Check cash balance
    account_details = client.get(f"/accounts/{account_id}/").json()
    assert account_details["cash_balance"] == 2000.0 - 750.0 # 1250.0

    # Check holdings
    holdings_response = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert len(holdings) == 1
    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[0]["quantity"] == 5.0
    assert holdings[0]["average_price"] == 150.0

    # Buy more AAPL to test average price (price is still 150.00)
    buy_more_aapl_response = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 3.0})
    assert buy_more_aapl_response.status_code == 200
    
    # Check cash balance again
    account_details = client.get(f"/accounts/{account_id}/").json()
    assert account_details["cash_balance"] == 1250.0 - (3 * 150.0) # 1250 - 450 = 800.0

    # Check holdings - quantity and average price should update
    holdings_response = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert len(holdings) == 1
    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[0]["quantity"] == 8.0 # 5 + 3
    # Average price should remain 150.0 since price didn't change
    assert holdings[0]["average_price"] == 150.0

    # Buy with insufficient funds
    # Current cash: 800.0. TSLA price 800.00. Buying 2.0 quantity costs 1600.00
    insufficient_funds_buy = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "TSLA", "quantity": 2.0}) 
    assert insufficient_funds_buy.status_code == 400
    assert insufficient_funds_buy.json() == {"detail": "Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity."}

    # Buy zero or negative quantity
    bad_quantity_buy = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 0.0})
    assert bad_quantity_buy.status_code == 400
    assert bad_quantity_buy.json() == {"detail": "Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity."}

    bad_quantity_buy = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": -1.0})
    assert bad_quantity_buy.status_code == 400
    assert bad_quantity_buy.json() == {"detail": "Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity."}

    # Buy invalid symbol
    invalid_symbol_buy = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "XYZ", "quantity": 1.0})
    assert invalid_symbol_buy.status_code == 400
    assert invalid_symbol_buy.json() == {"detail": "Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity."}

    # Buy for non-existent account
    non_existent_buy = client.post("/accounts/9999/buy/", json={"symbol": "AAPL", "quantity": 1.0})
    assert non_existent_buy.status_code == 400
    assert non_existent_buy.json() == {"detail": "Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity."}


def test_sell_stock(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 2000.0})
    account_id = create_response.json()["id"]

    # Buy some AAPL first to have something to sell
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 10.0}) # Cost 1500.0, balance 500.0
    
    # Attempt to buy TSLA, this should fail due to insufficient funds (balance 500, TSLA 800)
    fail_buy_tsla = client.post(f"/accounts/{account_id}/buy/", json={"symbol": "TSLA", "quantity": 1.0}) 
    assert fail_buy_tsla.status_code == 400
    account_details_after_failed_buy = client.get(f"/accounts/{account_id}/").json()
    assert account_details_after_failed_buy["cash_balance"] == 500.0 # Balance should not have changed

    # Sell some AAPL (partial)
    sell_aapl_response = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 4.0})
    assert sell_aapl_response.status_code == 200
    sell_data = sell_aapl_response.json()
    assert sell_data["type"] == "SELL"
    assert sell_data["symbol"] == "AAPL"
    assert sell_data["quantity"] == 4.0
    assert sell_data["price"] == 150.0
    assert sell_data["amount"] == 600.0 # 4 * 150.0

    # Check cash balance
    account_details = client.get(f"/accounts/{account_id}/").json()
    assert account_details["cash_balance"] == 500.0 + 600.0 # 1100.0

    # Check holdings
    holdings_response = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert len(holdings) == 1
    assert holdings[0]["symbol"] == "AAPL"
    assert holdings[0]["quantity"] == 6.0 # 10 - 4
    assert holdings[0]["average_price"] == 150.0 # Average price doesn't change on sell

    # Sell remaining AAPL (all shares)
    sell_all_aapl_response = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 6.0})
    assert sell_all_aapl_response.status_code == 200

    # Check cash balance
    account_details = client.get(f"/accounts/{account_id}/").json()
    assert account_details["cash_balance"] == 1100.0 + (6 * 150.0) # 1100 + 900 = 2000.0

    # Check holdings - AAPL holding should be deleted
    holdings_response = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert len(holdings) == 0 # No more AAPL holding

    # Sell more shares than owned (for a stock not owned)
    not_enough_shares_sell = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "GOOGL", "quantity": 1.0})
    assert not_enough_shares_sell.status_code == 400
    assert not_enough_shares_sell.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}

    # Sell more shares than owned (for a stock that was once owned but now is zero)
    not_enough_shares_sell_aapl = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 1.0})
    assert not_enough_shares_sell_aapl.status_code == 400
    assert not_enough_shares_sell_aapl.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}


    # Sell zero or negative quantity
    bad_quantity_sell = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 0.0})
    assert bad_quantity_sell.status_code == 400
    assert bad_quantity_sell.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}

    bad_quantity_sell = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": -1.0})
    assert bad_quantity_sell.status_code == 400
    assert bad_quantity_sell.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}

    # Sell invalid symbol
    invalid_symbol_sell = client.post(f"/accounts/{account_id}/sell/", json={"symbol": "XYZ", "quantity": 1.0})
    assert invalid_symbol_sell.status_code == 400
    assert invalid_symbol_sell.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}

    # Sell for non-existent account
    non_existent_sell = client.post("/accounts/9999/sell/", json={"symbol": "AAPL", "quantity": 1.0})
    assert non_existent_sell.status_code == 400
    assert non_existent_sell.json() == {"detail": "Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity."}


def test_get_holdings(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 5000.0})
    account_id = create_response.json()["id"]

    # No holdings initially
    holdings_response_empty = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response_empty.status_code == 200
    assert holdings_response_empty.json() == []

    # Buy some stocks
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 5.0}) # 5 * 150 = 750
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "GOOGL", "quantity": 1.0}) # 1 * 2500 = 2500

    holdings_response = client.get(f"/accounts/{account_id}/holdings/")
    assert holdings_response.status_code == 200
    holdings = holdings_response.json()
    assert len(holdings) == 2

    aapl_holding = next(h for h in holdings if h["symbol"] == "AAPL")
    assert aapl_holding["quantity"] == 5.0
    assert aapl_holding["average_price"] == 150.0

    googl_holding = next(h for h in holdings if h["symbol"] == "GOOGL")
    assert googl_holding["quantity"] == 1.0
    assert googl_holding["average_price"] == 2500.0

    # Get holdings for non-existent account
    non_existent_holdings = client.get("/accounts/9999/holdings/")
    assert non_existent_holdings.status_code == 404
    assert non_existent_holdings.json() == {"detail": "Account not found"}


def test_get_transactions(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 1000.0})
    account_id = create_response.json()["id"]

    # Initial deposit
    transactions_response = client.get(f"/accounts/{account_id}/transactions/")
    assert transactions_response.status_code == 200
    transactions = transactions_response.json()
    assert len(transactions) == 1
    assert transactions[0]["type"] == "DEPOSIT"
    assert transactions[0]["amount"] == 1000.0

    # Perform more transactions
    client.post(f"/accounts/{account_id}/deposit/", json={"amount": 200.0})
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 1.0}) # 150
    client.post(f"/accounts/{account_id}/withdraw/", json={"amount": 50.0})
    client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 0.5}) # 75

    transactions_response_full = client.get(f"/accounts/{account_id}/transactions/")
    assert transactions_response_full.status_code == 200
    full_transactions = transactions_response_full.json()
    
    # Expected transactions: initial_deposit, deposit (200), buy, withdraw, sell. Total 5
    # The initial_deposit transaction is recorded during account creation.
    # So, create account (1 transaction), deposit (1), buy (1), withdraw (1), sell (1) = 5 transactions.
    # The order is newest first.
    assert len(full_transactions) == 5
    
    # Verify order (newest first) and types
    assert full_transactions[0]["type"] == "SELL"
    assert full_transactions[1]["type"] == "WITHDRAWAL"
    assert full_transactions[2]["type"] == "BUY"
    assert full_transactions[3]["type"] == "DEPOSIT" # The 200.0 deposit
    assert full_transactions[4]["type"] == "DEPOSIT" # The initial 1000.0 deposit


    # Get transactions for non-existent account
    non_existent_transactions = client.get("/accounts/9999/transactions/")
    assert non_existent_transactions.status_code == 404
    assert non_existent_transactions.json() == {"detail": "Account not found"}


def test_get_portfolio_summary(client):
    create_response = client.post("/accounts/", json={"initial_deposit": 2000.0})
    account_id = create_response.json()["id"]

    # Summary with cash only
    summary_cash_only = client.get(f"/accounts/{account_id}/portfolio-summary/")
    assert summary_cash_only.status_code == 200
    data = summary_cash_only.json()
    assert data["account_id"] == account_id
    assert data["cash_balance"] == 2000.0
    assert data["stock_holdings_value"] == 0.0
    assert data["total_portfolio_value"] == 2000.0
    assert data["initial_deposit"] == 2000.0
    assert data["profit_loss"] == 0.0

    # Buy some stocks
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "AAPL", "quantity": 5.0}) # Cost 750, cash 1250
    client.post(f"/accounts/{account_id}/buy/", json={"symbol": "TSLA", "quantity": 1.0}) # Cost 800, cash 450

    # Summary with cash and stocks
    summary_with_stocks = client.get(f"/accounts/{account_id}/portfolio-summary/")
    assert summary_with_stocks.status_code == 200
    data = summary_with_stocks.json()
    assert data["account_id"] == account_id
    assert data["cash_balance"] == 450.0
    
    # Current stock prices: AAPL 150.00, TSLA 800.00
    expected_stock_value = (5 * 150.0) + (1 * 800.0) # 750 + 800 = 1550.0
    assert data["stock_holdings_value"] == expected_stock_value
    
    expected_total_value = 450.0 + expected_stock_value # 450 + 1550 = 2000.0
    assert data["total_portfolio_value"] == expected_total_value
    assert data["initial_deposit"] == 2000.0
    # Profit/loss should be total_portfolio_value - initial_deposit = 2000.0 - 2000.0 = 0.0
    assert data["profit_loss"] == pytest.approx(0.0) # Use pytest.approx for float comparison

    # Deposit more funds, should increase cash balance and P/L
    client.post(f"/accounts/{account_id}/deposit/", json={"amount": 500.0}) # Balance 950
    summary_after_deposit = client.get(f"/accounts/{account_id}/portfolio-summary/")
    assert summary_after_deposit.status_code == 200
    data = summary_after_deposit.json()
    assert data["cash_balance"] == 950.0
    assert data["stock_holdings_value"] == expected_stock_value
    expected_total_value_after_deposit = 950.0 + expected_stock_value # 950 + 1550 = 2500.0
    assert data["total_portfolio_value"] == expected_total_value_after_deposit
    assert data["profit_loss"] == pytest.approx(expected_total_value_after_deposit - data["initial_deposit"]) # 2500 - 2000 = 500.0

    # Sell some stocks, should increase cash balance and affect P/L
    client.post(f"/accounts/{account_id}/sell/", json={"symbol": "AAPL", "quantity": 2.0}) # Sale 2 * 150 = 300, cash balance 950 + 300 = 1250
    summary_after_sell = client.get(f"/accounts/{account_id}/portfolio-summary/")
    assert summary_after_sell.status_code == 200
    data = summary_after_sell.json()
    assert data["cash_balance"] == 1250.0
    
    expected_stock_value_after_sell = (3 * 150.0) + (1 * 800.0) # 450 + 800 = 1250.0 (3 AAPL remaining)
    assert data["stock_holdings_value"] == expected_stock_value_after_sell
    assert data["total_portfolio_value"] == 1250.0 + expected_stock_value_after_sell # 1250 + 1250 = 2500.0
    assert data["profit_loss"] == pytest.approx(2500.0 - data["initial_deposit"]) # 2500 - 2000 = 500.0


    # Get summary for non-existent account
    non_existent_summary = client.get("/accounts/9999/portfolio-summary/")
    assert non_existent_summary.status_code == 404
    assert non_existent_summary.json() == {"detail": "Account not found or unable to calculate summary."}
