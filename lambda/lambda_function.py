from datetime import datetime
import urllib3
import json
from config import PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL


def get_eod_adj_close_price(asset_ticker) -> tuple[float, str, float]:
    http = urllib3.PoolManager()
    url = f"https://eodhd.com/api/eod/{asset_ticker}?api_token={EODHD_API_KEY}&fmt=json&order=d"
    response = http.request("GET", url)
    data = json.loads(response.data.decode("utf-8"))

    current_adj_close_price: float = data[0]["adjusted_close"]
    current_adj_close_date: str = data[0]["date"]

    prev_adj_close_price: float = data[1]["adjusted_close"]

    return current_adj_close_price, current_adj_close_date, prev_adj_close_price


def calculate_portfolio_value():
    total_value = 0

    for asset in PORTFOLIO:
        asset_ticker: str = asset["asset_ticker"]
        asset_quantity: float = asset["quantity"]

        if asset_ticker == "cash":
            total_value += asset_quantity
        else:
            current_adj_close_price, current_adj_close_date, _ = get_eod_adj_close_price(
                asset_ticker
            )
            if current_adj_close_price == 0.0:
                continue
            total_asset_value: float = round(current_adj_close_price * asset_quantity, 2)
            total_value += total_asset_value

    return total_value, current_adj_close_date


def send_webhook_message(message) -> int:
    try:
        http = urllib3.PoolManager()
        data = {"content": message}
        encoded_data = json.dumps(data).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        response = http.request(
            "POST",
            WEBHOOK_URL,
            body=encoded_data,
            headers=headers,
        )
        return response.status
    except Exception as e:
        return 500


def lambda_handler(event, context):
    total_value, date_time = calculate_portfolio_value()

    fmtd_total_value = f"£{total_value:,.2f}"
    fmtd_date_time = datetime.strptime(date_time, "%Y-%m-%d").strftime("%d %B %Y")

    message = f"Total Value: {fmtd_total_value}\nLast Close: {fmtd_date_time}"

    send_webhook_message(message)
