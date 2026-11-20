from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .services import get_stock_price # Import the service for stock prices

def create_account(db: Session, account_in: schemas.AccountCreate) -> models.Account:
    db_account = models.Account(
        initial_deposit=account_in.initial_deposit,
        cash_balance=account_in.initial_deposit
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    # Record the initial deposit as a transaction
    transaction = models.Transaction(
        account_id=db_account.id,
        type="DEPOSIT",
        amount=account_in.initial_deposit,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

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
        type="DEPOSIT",
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
        type="WITHDRAWAL",
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

    current_price = get_stock_price(symbol=symbol)
    if current_price is None:
        return None # Invalid symbol or price not found
    
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
        type="BUY",
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

    current_price = get_stock_price(symbol=symbol)
    if current_price is None:
        return None # Invalid symbol or price not found
    
    total_sale_amount = current_price * quantity

    account.cash_balance += total_sale_amount
    holding.quantity -= quantity

    if holding.quantity == 0:
        db.delete(holding)
    
    transaction = models.Transaction(
        account_id=account.id,
        type="SELL",
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
    if holding.quantity > 0: # Check if the holding still exists before refreshing
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

    stock_holdings_value = 0.0
    
    for holding in holdings:
        current_price = get_stock_price(symbol=holding.symbol)
        if current_price is None:
            # If price cannot be retrieved, treat its current value as 0 for summary purposes
            # Or log a warning. For now, we'll skip its contribution to market value.
            continue
        stock_holdings_value += holding.quantity * current_price

    total_portfolio_value = cash_balance + stock_holdings_value
    
    # Calculate profit/loss relative to initial deposit
    # This considers initial deposit as the baseline
    # Total value of portfolio (cash + stocks) minus the initial cash put in
    profit_loss = total_portfolio_value - account.initial_deposit

    return schemas.PortfolioSummaryResponse(
        account_id=account.id,
        cash_balance=cash_balance,
        stock_holdings_value=stock_holdings_value,
        total_portfolio_value=total_portfolio_value,
        profit_loss=profit_loss,
        initial_deposit=account.initial_deposit
    )
