from typing import Optional

# Fixed test prices for AAPL, TSLA, and GOOGL
STOCK_PRICES = {
    "AAPL": 150.0,
    "TSLA": 200.0,
    "GOOGL": 100.0,
}


def get_share_price(symbol: str) -> Optional[float]:
    """
    Returns the fixed test price for the given stock symbol.
    Returns None if the symbol is not supported.
    """
    if not symbol:
        return None
    return STOCK_PRICES.get(symbol.strip().upper())
