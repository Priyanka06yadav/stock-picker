
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/accounts/", response_model=schemas.AccountResponse, status_code=201)
def create_account_endpoint(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    """Create a new trading account with an initial deposit."""
    db_account = crud.create_account(db=db, account_in=account)
    return db_account

@app.get("/accounts/{account_id}/", response_model=schemas.AccountResponse)
def read_account_endpoint(account_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific trading account."""
    account = crud.get_account(db, account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.post("/accounts/{account_id}/deposit/", response_model=schemas.AccountResponse)
def deposit_funds_endpoint(account_id: int, deposit: schemas.DepositWithdraw, db: Session = Depends(get_db)):
    """Deposit funds into a trading account."""
    account = crud.deposit_funds(db, account_id=account_id, amount=deposit.amount)
    if account is None:
        raise HTTPException(status_code=400, detail="Unable to deposit funds. Check amount.")
    return account

@app.post("/accounts/{account_id}/withdraw/", response_model=schemas.AccountResponse)
def withdraw_funds_endpoint(account_id: int, withdraw: schemas.DepositWithdraw, db: Session = Depends(get_db)):
    """Withdraw funds from a trading account."""
    account = crud.withdraw_funds(db, account_id=account_id, amount=withdraw.amount)
    if account is None:
        raise HTTPException(status_code=400, detail="Unable to withdraw funds. Insufficient cash or invalid amount.")
    return account

@app.post("/accounts/{account_id}/buy/", response_model=schemas.TransactionResponse)
def buy_stock_endpoint(account_id: int, buy: schemas.BuySellStock, db: Session = Depends(get_db)):
    """Buy shares of a stock for a trading account."""
    transaction = crud.buy_stock(db, account_id=account_id, symbol=buy.symbol, quantity=buy.quantity)
    if transaction is None:
        raise HTTPException(status_code=400, detail="Unable to buy stock. Insufficient funds, invalid symbol, or invalid quantity.")
    return transaction

@app.post("/accounts/{account_id}/sell/", response_model=schemas.TransactionResponse)
def sell_stock_endpoint(account_id: int, sell: schemas.BuySellStock, db: Session = Depends(get_db)):
    """Sell shares of a stock from a trading account."""
    transaction = crud.sell_stock(db, account_id=account_id, symbol=sell.symbol, quantity=sell.quantity)
    if transaction is None:
        raise HTTPException(status_code=400, detail="Unable to sell stock. Not enough shares, invalid symbol, or invalid quantity.")
    return transaction

@app.get("/accounts/{account_id}/holdings/", response_model=List[schemas.HoldingResponse])
def get_holdings_endpoint(account_id: int, db: Session = Depends(get_db)):
    """Get current stock holdings for a trading account."""
    account = crud.get_account(db, account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    holdings = crud.get_holdings(db, account_id=account_id)
    return holdings

@app.get("/accounts/{account_id}/transactions/", response_model=List[schemas.TransactionResponse])
def get_transactions_endpoint(account_id: int, db: Session = Depends(get_db)):
    """Get transaction history for a trading account."""
    account = crud.get_account(db, account_id=account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    transactions = crud.get_transactions(db, account_id=account_id)
    return transactions

@app.get("/accounts/{account_id}/portfolio-summary/", response_model=schemas.PortfolioSummaryResponse)
def get_portfolio_summary_endpoint(account_id: int, db: Session = Depends(get_db)):
    """Get a summary of the portfolio, including cash balance, stock value, total value, and profit/loss."""
    summary = crud.calculate_portfolio_summary(db, account_id=account_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Account not found or unable to calculate summary.")
    return summary
