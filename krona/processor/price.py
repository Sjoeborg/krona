from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from yfinance.const import USER_AGENTS


@dataclass
class SearchResult:
    symbol: str
    exchange: str
    name: str


@dataclass
class Price:
    date: datetime
    price: float
    currency: str


class PriceClient:
    def __init__(self):
        self.session = httpx.AsyncClient(headers={"User-Agent": USER_AGENTS[0]})

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response and JSON parsing with consistent error handling."""
        if response.status_code != 200:
            raise Exception(f"Failed to call Yahoo Finance API at {response.url}: {response.text}")

        try:
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to parse response from {response.url}: {response.text}") from e

    async def search(self, query: str) -> SearchResult:
        res = await self.session.get("https://query2.finance.yahoo.com/v1/finance/search", params={"q": query})
        data = await self._handle_response(res)

        if data["count"] != 1:
            raise Exception(f"Expected 1 result for {query}, got {data['count']}")

        return SearchResult(
            symbol=data["quotes"][0]["symbol"],
            exchange=data["quotes"][0]["exchange"],
            name=data["quotes"][0]["shortname"],
        )

    async def get_price(
        self, symbol: str, interval: str = "1d", since: str | None = None, date_range: tuple[str, str] | None = None
    ) -> list[Price]:
        params = {"interval": interval, "includePrePost": False}
        if not since and not date_range:
            raise Exception("Either since or date_range must be provided")

        if since:
            params["range"] = since
        if date_range:
            params["period1"] = datetime.strptime(date_range[0], "%Y-%m-%d").timestamp()
            params["period2"] = datetime.strptime(date_range[1], "%Y-%m-%d").timestamp()

        res = await self.session.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}", params=params)
        data = await self._handle_response(res)

        try:
            if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                return self._extract_price_from_response(data)

            raise Exception(f"Could not extract price from response for {symbol}")
        except (KeyError, IndexError, ValueError) as e:
            raise Exception(f"Failed to parse price data for {symbol}: {e!s}") from e

    def _extract_price_from_response(self, data: dict[str, Any]) -> list[Price]:
        """Parse the YF response into a list of Price objects"""
        result = data["chart"]["result"][0]
        quotes = result["indicators"]["quote"][0]
        print(result)
        close_prices = [round(p, 4) for p in quotes["close"] if p is not None]
        timestamps = [p for p in result["timestamp"] if p is not None]  # list of e.g. 1718294400
        currency = result["meta"]["currency"]
        return [
            Price(date=datetime.fromtimestamp(t), price=p, currency=currency)
            for t, p in zip(timestamps, close_prices, strict=True)
        ]


def convert_price(price: Price, currencies: list[Price]) -> Price:
    for curr in currencies:
        if price.date.date() == curr.date.date():
            return Price(date=price.date, price=round(price.price * curr.price, 4), currency=curr.currency)
    raise Exception(f"Could not find currency for {price.date} in {currencies}")


async def main():
    client = PriceClient()
    res = await client.search("SE0000107419")
    print(res)
    prices = await client.get_price(res.symbol, since="1mo")
    currencies = await client.get_price("SEK=X", since="1mo")
    for price in prices:
        print(convert_price(price, currencies))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
