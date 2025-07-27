import httpx


class PriceClient:
    def __init__(self, api_key: str):
        self.client = httpx.Client()
        self.api_key = api_key

    def get_price(self, ticker: str, date: str) -> float:
        response = self.client.get(
            f"https://api.polygon.io/v3/reference/tickers/{ticker}",
            params={"apiKey": self.api_key, "date": date},
        )
        return response.json()["results"]["market_cap"] / response.json()["results"]["share_class_shares_outstanding"]


p = PriceClient(api_key="V3vw4Fb1GpK4PZKMoQBCuIyJnJuzD3g3")

print(p.get_price("AAPL", "2025-07-25"))
