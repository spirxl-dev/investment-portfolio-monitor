from logging import getLogger, INFO
from datetime import datetime, timedelta
import urllib3
import json
from config import PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL

logger = getLogger()
logger.setLevel(INFO)


def get_eod_adjusted_close_price(asset_ticker, asset_name) -> float:
    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        http = urllib3.PoolManager()
        url = f"https://eodhd.com/api/eod/{asset_ticker}?api_token={EODHD_API_KEY}&fmt=json&from={yesterday}&to={today}"
        response = http.request("GET", url)
        data = json.loads(response.data.decode("utf-8"))
        adjusted_close_price = data[0]["adjusted_close"]
        logger.info(
            f"Fetched adjusted close price for {asset_name}: £{adjusted_close_price}"
        )
    except Exception as e:
        logger.error(f"Error fetching data for {asset_name}: {e}")
        return 0.0

    return adjusted_close_price


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
            adjusted_close_price = get_eod_adjusted_close_price(
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
    return total_value


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
    logger.info("Lambda function invoked.")
    total_value = calculate_portfolio_value()
    formatted_value = f"£{total_value:,.2f}"
    message = f"Total Portfolio Value: {formatted_value}"

    send_webhook_message(message)
    logger.info("Lambda function completed.")
