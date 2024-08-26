from datetime import datetime
from logging import getLogger, INFO
import urllib3
import json
from config import PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL

logger = getLogger()
logger.setLevel(INFO)


def get_eod_adj_close_price(asset_ticker, asset_name) -> tuple[int, str]:
    http = urllib3.PoolManager()
    url = f"https://eodhd.com/api/eod/{asset_ticker}?api_token={EODHD_API_KEY}&fmt=json&order=d"
    response = http.request("GET", url)
    data = json.loads(response.data.decode("utf-8"))
    adj_close_price: int = data[0]["adjusted_close"]
    adj_close_date: str = data[0]["date"]
    logger.info(f"Adjusted close price for {asset_name}: £{adj_close_price}")

    return adj_close_price, adj_close_date 


def calculate_portfolio_value() -> float:
    total_value = 0

    for asset in PORTFOLIO:
        asset_name = asset["asset_name"]
        asset_ticker = asset["asset_ticker"]
        asset_quantity = asset["quantity"]

        if asset_ticker == "cash":
            logger.info(f"Adding cash to total value: £{asset_quantity}")
            total_value += asset_quantity
        else:
            adjusted_close_price, adjusted_close_price_date = get_eod_adj_close_price(
                asset_ticker, asset_name
            )
            if adjusted_close_price == 0.0:
                logger.warning(f"Skipped {asset_ticker} due to missing price data.")
                continue
            total_asset_value = round(adjusted_close_price * asset_quantity, 2)
            logger.info(
                f"Total value of {asset_quantity} units of {asset_name}: £{total_asset_value:,.2f}"
            )
            total_value += total_asset_value

    logger.info(f"Total portfolio value calculated: {total_value:,.2f}")
    return total_value, adjusted_close_price_date


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
        logger.info(f"Webhook message sent. Response status: {response.status}")
        return response.status
    except Exception as e:
        logger.error(f"Error sending webhook message: {e}")
        return 500


def lambda_handler(event, context):
    total_value, date_time = calculate_portfolio_value()

    fmtd_total_value = f"£{total_value:,.2f}"
    fmtd_date_time = datetime.strptime(date_time, "%Y-%m-%d").strftime("%d %B %Y")

    message = f"Total Value: {fmtd_total_value}\nLast Close: {fmtd_date_time}"

    send_webhook_message(message)
