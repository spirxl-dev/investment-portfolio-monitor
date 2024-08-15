from datetime import datetime, timedelta
import urllib3
import json
from config import PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL


def get_eod_adjusted_close_price(ticker) -> float:
    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        http = urllib3.PoolManager()
        url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_API_KEY}&fmt=json&from={yesterday}&to={today}"
        response = http.request("GET", url)
        data = json.loads(response.data.decode("utf-8"))
        adjusted_close_price = data[0]["adjusted_close"]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return 0.0

    return adjusted_close_price


def calculate_portfolio_value() -> float:
    total_value = 0

    for asset in PORTFOLIO:
        asset_name = asset["asset_name"]
        asset_ticker = asset["asset_ticker"]
        quantity = asset["quantity"]

        if asset_name == "cash":
            total_value += quantity
        else:
            adjusted_close_price = get_eod_adjusted_close_price(asset_ticker)
            total_asset_value = round(adjusted_close_price * quantity, 2)
            total_value += total_asset_value

    return total_value


def send_webhook_message(message) -> int:

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


def lambda_handler(event, context):
    total_value = calculate_portfolio_value()
    formatted_value = f"£{total_value:,.2f}"
    message = f"Total Portfolio Value: {formatted_value}"

    send_webhook_message(message)
