from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

# Assuming models.py and schemas.py are in the same directory or accessible via path
from . import models, schemas

# This will be replaced by the tool call
# The instruction says "You must use the provided get_share_price(symbol) function for retrieving stock prices."
# The tool is `default_api.get_stock_price`.

def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    db_account = models.Account(username=account.username, cash_balance=0.0)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def get_account(db: Session, account_id: int) -> Optional[models.Account]:
    return db.query(models.Account).filter(models.Account.id == account_id).first()

def deposit_funds(db: Session, account_id: int, amount: float) -> Optional[models.Account]:
    if amount <= 0:
        return None # Cannot deposit non-positive amount

    account = get_account(db, account_id)
    if not account:
        return None

    account.cash_balance += amount
    
    transaction = models.Transaction(
        account_id=account.id,
        transaction_type="DEPOSIT",
        amount=amount,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(account)
    db.refresh(transaction)
    return account

def withdraw_funds(db: Session, account_id: int, amount: float) -> Optional[models.Account]:
    if amount <= 0:
        return None # Cannot withdraw non-positive amount

    account = get_account(db, account_id)
    if not account:
        return None

    if account.cash_balance < amount:
        return None # Insufficient funds

    account.cash_balance -= amount

    transaction = models.Transaction(
        account_id=account.id,
        transaction_type="WITHDRAWAL",
        amount=amount,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(account)
    db.refresh(transaction)
    return account

def buy_stock(db: Session, account_id: int, symbol: str, quantity: float) -> Optional[models.Transaction]:
    if quantity <= 0:
        return None

    account = get_account(db, account_id)
    if not account:
        return None

    # Get stock price using the provided tool
    stock_price_response = default_api.get_stock_price(symbol=symbol)
    if not stock_price_response or 'price' not in stock_price_response:
        print(f"Could not retrieve price for symbol: {symbol}")
        return None
    
    current_price = stock_price_response['price']
    total_cost = current_price * quantity

    if account.cash_balance < total_cost:
        return None # Insufficient funds

    account.cash_balance -= total_cost

    # Update or create holding
    holding = db.query(models.Holding).filter(
        models.Holding.account_id == account_id,
        models.Holding.symbol == symbol
    ).first()

    if holding:
        # Calculate new average price
        new_total_quantity = holding.quantity + quantity
        new_total_cost = (holding.quantity * holding.average_price) + total_cost
        holding.average_price = new_total_cost / new_total_quantity
        holding.quantity = new_total_quantity
    else:
        holding = models.Holding(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            average_price=current_price
        )
        db.add(holding)
    
    transaction = models.Transaction(
        account_id=account.id,
        transaction_type="BUY",
        symbol=symbol,
        quantity=quantity,
        price=current_price,
        amount=total_cost,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(account)
    db.refresh(holding)
    db.refresh(transaction)
    return transaction

def sell_stock(db: Session, account_id: int, symbol: str, quantity: float) -> Optional[models.Transaction]:
    if quantity <= 0:
        return None

    account = get_account(db, account_id)
    if not account:
        return None

    holding = db.query(models.Holding).filter(
        models.Holding.account_id == account_id,
        models.Holding.symbol == symbol
    ).first()

    if not holding or holding.quantity < quantity:
        return None # Not enough shares to sell

    # Get stock price using the provided tool
    stock_price_response = default_api.get_stock_price(symbol=symbol)
    if not stock_price_response or 'price' not in stock_price_response:
        print(f"Could not retrieve price for symbol: {symbol}")
        return None
    
    current_price = stock_price_response['price']
    total_sale_amount = current_price * quantity

    account.cash_balance += total_sale_amount
    holding.quantity -= quantity

    if holding.quantity == 0:
        db.delete(holding)
    
    transaction = models.Transaction(
        account_id=account.id,
        transaction_type="SELL",
        symbol=symbol,
        quantity=quantity,
        price=current_price,
        amount=total_sale_amount,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(account)
    # If holding was deleted, it won't be refreshed. If it still exists, refresh it.
    if holding.quantity > 0:
        db.refresh(holding)
    db.refresh(transaction)
    return transaction

def get_holdings(db: Session, account_id: int) -> List[models.Holding]:
    return db.query(models.Holding).filter(models.Holding.account_id == account_id).all()

def get_transactions(db: Session, account_id: int) -> List[models.Transaction]:
    return db.query(models.Transaction).filter(
        models.Transaction.account_id == account_id
    ).order_by(models.Transaction.timestamp.desc()).all() # Order by newest first

def calculate_portfolio_summary(db: Session, account_id: int) -> Optional[schemas.PortfolioSummaryResponse]:
    account = get_account(db, account_id)
    if not account:
        return None

    cash_balance = account.cash_balance
    holdings = get_holdings(db, account_id)

    current_stock_value = 0.0
    total_invested_in_stocks = 0.0
    
    for holding in holdings:
        # Get stock price using the provided tool
        stock_price_response = default_api.get_stock_price(symbol=holding.symbol)
        if not stock_price_response or 'price' not in stock_price_response:
            print(f"Could not retrieve price for symbol: {holding.symbol}. Skipping this holding from portfolio calculation.")
            continue
        
        current_price = stock_price_response['price']
        current_stock_value += holding.quantity * current_price
        total_invested_in_stocks += holding.quantity * holding.average_price

    total_portfolio_value = cash_balance + current_stock_value
    total_gain_loss = current_stock_value - total_invested_in_stocks
    
    percentage_gain_loss = 0.0
    if total_invested_in_stocks > 0:
        percentage_gain_loss = (total_gain_loss / total_invested_in_stocks) * 100

    return schemas.PortfolioSummaryResponse(
        account_id=account.id,
        cash_balance=cash_balance,
        total_portfolio_value=total_portfolio_value,
        total_invested_in_stocks=total_invested_in_stocks,
        current_stock_value=current_stock_value,
        total_gain_loss=total_gain_loss,
        percentage_gain_loss=percentage_gain_loss
    )
