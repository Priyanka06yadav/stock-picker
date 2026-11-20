from sqlalchemy import Column, Float, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    initial_deposit = Column(Float, nullable=False)
    cash_balance = Column(Float, default=0.0)

    holdings = relationship("Holding", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    symbol = Column(String, index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)

    account = relationship("Account", back_populates="holdings")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    type = Column(String, nullable=False) # e.g., 'deposit', 'withdrawal', 'buy', 'sell'
    symbol = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    amount = Column(Float, nullable=False) # The monetary value of the transaction
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="transactions")
