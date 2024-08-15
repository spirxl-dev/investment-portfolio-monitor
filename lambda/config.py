import os

PORTFOLIO: list = [
    {
        "asset_name": "Asset 1",
        "asset_ticker": "TICKER1.EXCHANGE",
        "quantity": 100,
        "currency": "GBP",
    },
    {
        "asset_name": "Asset 2",
        "asset_ticker": "TICKER2.EXCHANGE",
        "quantity": 50,
        "currency": "GBP",
    },
    {
        "asset_name": "cash",
        "asset_ticker": "",
        "quantity": 100.00,
        "currency": "GBP",
    },
]


WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
EODHD_API_KEY: str = os.getenv("EODHD_API_KEY", "")
