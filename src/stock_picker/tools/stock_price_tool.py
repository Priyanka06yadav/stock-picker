
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from stock_picker.tools.stock_prices import get_share_price


class StockPriceInput(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock ticker symbol, such as AAPL, TSLA, or GOOGL."
    )


class StockPriceTool(BaseTool):
    name: str = "Get Stock Price"

    description: str = (
        "Retrieves the fixed price of a supported stock symbol. "
        "Supported stocks are AAPL, TSLA, and GOOGL."
    )

    args_schema: type[BaseModel] = StockPriceInput

    def _run(self, symbol: str) -> str:
        try:
            price = get_share_price(symbol)
            return f"{symbol.upper()}: ${price:.2f}"
        except ValueError as e:
            return str(e)
