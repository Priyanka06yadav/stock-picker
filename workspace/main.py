import sqlite3
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# Database setup
DB_NAME = "portfolio.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        balance REAL DEFAULT 0.0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS holdings (
                        account_id INTEGER,
                        symbol TEXT,
                        quantity INTEGER,
                        PRIMARY KEY (account_id, symbol))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER,
                        type TEXT,
                        symbol TEXT,
                        quantity INTEGER,
                        price REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Stock Price Mock
def get_share_price(symbol: str) -> float:
    prices = {"AAPL": 150.0, "TSLA": 700.0, "GOOGL": 2800.0}
    return prices.get(symbol.upper(), 0.0)

# API Models
class AccountCreate(BaseModel):
    name: str

class TransactionRequest(BaseModel):
    amount: float

class TradeRequest(BaseModel):
    symbol: str
    quantity: int

# FastAPI App
app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.post("/accounts/")
def create_account(account: AccountCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (name, balance) VALUES (?, 0.0)", (account.name,))
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"account_id": account_id}

@app.post("/accounts/{account_id}/deposit")
def deposit(account_id: int, req: TransactionRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (req.amount, account_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: int, req: TransactionRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    balance = res[0]
    if balance < req.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds")
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (req.amount, account_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/accounts/{account_id}/buy")
def buy_stock(account_id: int, req: TradeRequest):
    price = get_share_price(req.symbol)
    if price == 0: raise HTTPException(status_code=404, detail="Invalid Symbol")
    total_cost = price * req.quantity
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    balance = res[0]
    if balance < total_cost:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (total_cost, account_id))
    cursor.execute("INSERT INTO holdings (account_id, symbol, quantity) VALUES (?, ?, ?) ON CONFLICT(account_id, symbol) DO UPDATE SET quantity = quantity + ?", 
                   (account_id, req.symbol, req.quantity, req.quantity))
    cursor.execute("INSERT INTO transactions (account_id, type, symbol, quantity, price) VALUES (?, 'BUY', ?, ?, ?)", 
                   (account_id, req.symbol, req.quantity, price))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/accounts/{account_id}/sell")
def sell_stock(account_id: int, req: TradeRequest):
    price = get_share_price(req.symbol)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM holdings WHERE account_id = ? AND symbol = ?", (account_id, req.symbol))
    row = cursor.fetchone()
    if not row or row[0] < req.quantity:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient shares")
    
    total_revenue = price * req.quantity
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (total_revenue, account_id))
    cursor.execute("UPDATE holdings SET quantity = quantity - ? WHERE account_id = ? AND symbol = ?", (req.quantity, account_id, req.symbol))
    cursor.execute("INSERT INTO transactions (account_id, type, symbol, quantity, price) VALUES (?, 'SELL', ?, ?, ?)", 
                   (account_id, req.symbol, req.quantity, price))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/accounts/{account_id}/portfolio")
def get_portfolio(account_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, quantity FROM holdings WHERE account_id = ?", (account_id,))
    holdings = [{"symbol": row[0], "quantity": row[1]} for row in cursor.fetchall()]
    
    total_value = sum(h['quantity'] * get_share_price(h['symbol']) for h in holdings)
    
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    balance = res[0]
    
    conn.close()
    return {"holdings": holdings, "total_portfolio_value": total_value + balance, "cash_balance": balance}

@app.get("/accounts/{account_id}/history")
def get_history(account_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT type, symbol, quantity, price, timestamp FROM transactions WHERE account_id = ?", (account_id,))
    history = [{"type": r[0], "symbol": r[1], "quantity": r[2], "price": r[3], "timestamp": r[4]} for r in cursor.fetchall()]
    conn.close()
    return history
