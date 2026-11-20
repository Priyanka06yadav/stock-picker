# Stock Portfolio Management Backend API

This document describes the backend API for the stock portfolio management application.

## Overview

The backend is built with FastAPI and Python, using SQLAlchemy for ORM and SQLite for persistent storage. It provides endpoints for managing user accounts, depositing/withdrawing funds, buying/selling stocks, viewing holdings, transaction history, and portfolio summary.

## Technologies Used

*   **Backend Framework**: FastAPI
*   **ORM**: SQLAlchemy
*   **Database**: SQLite
*   **Python Version**: 3.9+ (recommended)

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository-url>
    cd stock-portfolio-management
    ```
2.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```
4.  **Install dependencies:**
    ```bash
    pip install "fastapi[all]" uvicorn sqlalchemy pydantic
    ```
5.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Database Schema

The SQLite database (`sql_app.db`) consists of the following tables:

*   **`accounts`**: Stores user account information.
    *   `id` (Integer, Primary Key)
    *   `initial_deposit` (Float): The initial amount deposited when the account was created.
    *   `cash_balance` (Float): The current available cash.
*   **`holdings`**: Stores current stock holdings for each account.
    *   `id` (Integer, Primary Key)
    *   `account_id` (Integer, Foreign Key to `accounts.id`)
    *   `symbol` (String): Stock ticker symbol (e.g., AAPL).
    *   `quantity` (Float): Number of shares held.
    *   `average_price` (Float): Average purchase price per share.
*   **`transactions`**: Records all financial transactions.
    *   `id` (Integer, Primary Key)
    *   `account_id` (Integer, Foreign Key to `accounts.id`)
    *   `type` (String): Type of transaction (e.g., 'DEPOSIT', 'WITHDRAWAL', 'BUY', 'SELL').
    *   `symbol` (String, Nullable): Stock symbol for buy/sell transactions.
    *   `quantity` (Float, Nullable): Quantity of shares for buy/sell transactions.
    *   `price` (Float, Nullable): Price per share at the time of transaction for buy/sell.
    *   `amount` (Float): The monetary value of the transaction.
    *   `timestamp` (DateTime): Date and time of the transaction.

## API Endpoints

### 1. Create an Account

*   **POST** `/accounts/`
*   **Description**: Creates a new trading account with an initial deposit.
*   **Request Body**: `schemas.AccountCreate`
    ```json
    {
      "initial_deposit": 1000.00
    }
    ```
*   **Response Body**: `schemas.AccountResponse` (Status: 201 Created)
    ```json
    {
      "id": 1,
      "initial_deposit": 1000.0,
      "cash_balance": 1000.0
    }
    ```

### 2. Retrieve Account Details

*   **GET** `/accounts/{account_id}/`
*   **Description**: Retrieves the details of a specific trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Response Body**: `schemas.AccountResponse`
    ```json
    {
      "id": 1,
      "initial_deposit": 1000.0,
      "cash_balance": 1000.0
    }
    ```
*   **Error**: `404 Not Found` if account does not exist.

### 3. Deposit Funds

*   **POST** `/accounts/{account_id}/deposit/`
*   **Description**: Deposits funds into a trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Request Body**: `schemas.DepositWithdraw`
    ```json
    {
      "amount": 500.00
    }
    ```
*   **Response Body**: `schemas.AccountResponse` (updated account details)
    ```json
    {
      "id": 1,
      "initial_deposit": 1000.0,
      "cash_balance": 1500.0
    }
    ```
*   **Error**: `400 Bad Request` if amount is non-positive or account not found.

### 4. Withdraw Funds

*   **POST** `/accounts/{account_id}/withdraw/`
*   **Description**: Withdraws funds from a trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Request Body**: `schemas.DepositWithdraw`
    ```json
    {
      "amount": 200.00
    }
    ```
*   **Response Body**: `schemas.AccountResponse` (updated account details)
    ```json
    {
      "id": 1,
      "initial_deposit": 1000.0,
      "cash_balance": 1300.0
    }
    ```
*   **Error**: `400 Bad Request` if amount is non-positive, insufficient funds, or account not found.

### 5. Buy Stock

*   **POST** `/accounts/{account_id}/buy/`
*   **Description**: Buys shares of a stock for a trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Request Body**: `schemas.BuySellStock`
    ```json
    {
      "symbol": "AAPL",
      "quantity": 5.0
    }
    ```
*   **Response Body**: `schemas.TransactionResponse`
    ```json
    {
      "id": 1,
      "type": "BUY",
      "symbol": "AAPL",
      "quantity": 5.0,
      "price": 150.0,
      "amount": 750.0,
      "timestamp": "2023-10-27T10:00:00.123456"
    }
    ```
*   **Error**: `400 Bad Request` if insufficient funds, invalid symbol, non-positive quantity, or account not found.

### 6. Sell Stock

*   **POST** `/accounts/{account_id}/sell/`
*   **Description**: Sells shares of a stock from a trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Request Body**: `schemas.BuySellStock`
    ```json
    {
      "symbol": "AAPL",
      "quantity": 2.0
    }
    ```
*   **Response Body**: `schemas.TransactionResponse`
    ```json
    {
      "id": 2,
      "type": "SELL",
      "symbol": "AAPL",
      "quantity": 2.0,
      "price": 150.0,
      "amount": 300.0,
      "timestamp": "2023-10-27T10:05:00.123456"
    }
    ```
*   **Error**: `400 Bad Request` if not enough shares, invalid symbol, non-positive quantity, or account not found.

### 7. Get Current Stock Holdings

*   **GET** `/accounts/{account_id}/holdings/`
*   **Description**: Retrieves the current stock holdings for a trading account.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Response Body**: `List[schemas.HoldingResponse]`
    ```json
    [
      {
        "symbol": "AAPL",
        "quantity": 3.0,
        "average_price": 150.0
      },
      {
        "symbol": "TSLA",
        "quantity": 1.0,
        "average_price": 800.0
      }
    ]
    ```
*   **Error**: `404 Not Found` if account does not exist.

### 8. Get Transaction History

*   **GET** `/accounts/{account_id}/transactions/`
*   **Description**: Retrieves the complete transaction history for a trading account, ordered by newest first.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Response Body**: `List[schemas.TransactionResponse]`
    ```json
    [
      {
        "id": 2,
        "type": "SELL",
        "symbol": "AAPL",
        "quantity": 2.0,
        "price": 150.0,
        "amount": 300.0,
        "timestamp": "2023-10-27T10:05:00.123456"
      },
      {
        "id": 1,
        "type": "BUY",
        "symbol": "AAPL",
        "quantity": 5.0,
        "price": 150.0,
        "amount": 750.0,
        "timestamp": "2023-10-27T10:00:00.123456"
      },
      {
        "id": 0,
        "type": "DEPOSIT",
        "symbol": null,
        "quantity": null,
        "price": null,
        "amount": 1000.0,
        "timestamp": "2023-10-27T09:50:00.123456"
      }
    ]
    ```
*   **Error**: `404 Not Found` if account does not exist.

### 9. Get Portfolio Summary

*   **GET** `/accounts/{account_id}/portfolio-summary/`
*   **Description**: Provides a summary of the account's portfolio, including cash balance, current stock value, total portfolio value, and profit/loss compared to the initial deposit.
*   **Path Parameters**:
    *   `account_id` (int): The ID of the account.
*   **Response Body**: `schemas.PortfolioSummaryResponse`
    ```json
    {
      "account_id": 1,
      "cash_balance": 1300.0,
      "stock_holdings_value": 450.0,  # Example: 3 AAPL shares * 150.0
      "total_portfolio_value": 1750.0, # cash_balance + stock_holdings_value
      "profit_loss": 750.0,          # total_portfolio_value - initial_deposit (1750 - 1000)
      "initial_deposit": 1000.0
    }
    ```
*   **Error**: `404 Not Found` if account does not exist.

---
