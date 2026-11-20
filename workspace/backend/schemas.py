
from typing import List, Optional
from pydantic import BaseModel
import datetime

class AccountCreate(BaseModel):
    initial_deposit: float

class AccountResponse(BaseModel):
    id: int
    initial_deposit: float
    cash_balance: float

    class Config:
        orm_mode = True

class DepositWithdraw(BaseModel):
    amount: float

class BuySellStock(BaseModel):
    symbol: str
    quantity: float

class HoldingResponse(BaseModel):
    symbol: str
    quantity: float
    average_price: float

    class Config:
        orm_mode = True

class TransactionResponse(BaseModel):
    id: int
    type: str
    symbol: Optional[str]
    quantity: Optional[float]
    price: Optional[float]
    amount: float
    timestamp: datetime.datetime

    class Config:
        orm_mode = True

class PortfolioSummaryResponse(BaseModel):
    account_id: int
    cash_balance: float
    stock_holdings_value: float
    total_portfolio_value: float
    profit_loss: float
    initial_deposit: float

