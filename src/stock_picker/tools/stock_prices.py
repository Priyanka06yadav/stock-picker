
STOCK_PRICES = {
    "AAPL": 200.0,
    "TSLA": 250.0,
    "GOOGL": 150.0,
}


def get_share_price(symbol: str) -> float:
    """
    Return the fixed test price for a supported stock symbol.
    """

    symbol = symbol.strip().upper()

    if symbol not in STOCK_PRICES:
        raise ValueError(
            f"Unsupported stock symbol: {symbol}"
        )

    return STOCK_PRICES[symbol]
