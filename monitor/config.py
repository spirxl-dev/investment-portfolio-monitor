import os

VANGUARD_PORTFOLIO: list = [
    {
        "asset_name": "Vanguard S&P 500 UCITS ETF USD Acc",
        "asset_ticker": "VUAG.LSE",
        "quantity": 0,
        "currency": "GBP",
    },
    {
        "asset_name": "British Pound",
        "asset_ticker": "cash",
        "quantity": 0,
        "currency": "GBP",
    },
]

AJ_BELL_PORTFOLIO: list = [
    {
        "asset_name": "HSBC FTSE ALL WORLD INDEX",
        "quantity": 0,
        "currency": "GBP",
    }
]


WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
EODHD_API_KEY: str = os.getenv("EODHD_API_KEY", "")
