import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    cash_balance = Column(Float, default=0.0, nullable=False)
    initial_deposit = Column(Float, default=0.0, nullable=False)
    total_deposited = Column(Float, default=0.0, nullable=False)
    total_withdrawn = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    holdings = relationship("Holding", back_populates="account", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)

    account = relationship("Account", back_populates="holdings")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    transaction_type = Column(String, nullable=False)  # DEPOSIT, WITHDRAWAL, BUY, SELL
    symbol = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    price_per_share = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    account = relationship("Account", back_populates="transactions")
