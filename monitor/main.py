import json
import time
import re
from datetime import datetime
import urllib3
from lxml import html
import pytz
import logging
from config import VANGUARD_PORTFOLIO, AJ_BELL_PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def calculate_aj_bell_dodl_portfolio_value():
    def _get_hsbc_ftse_all_world_price(quantity: float) -> float:
        try:
            logging.info("Fetching HSBC FTSE All-World price.")
            http = urllib3.PoolManager()
            response = http.request(
                "GET",
                "https://www.fidelity.co.uk/factsheet-data/factsheet/GB00BMJJJF91-hsbc-ftse-all-world-index-c-acc/key-statistics",
            )
            tree = html.fromstring(response.data)

            element = tree.xpath(
                '//*[@id="__next"]/div/div[1]/div[1]/div[1]/div[2]/div[1]/div/div/div[1]/h3'
            )
            price = float(re.sub(r"[^0-9.]", "", element[0].text.strip()))
            total_value = quantity * price
            logging.info(f"Fetched price: {price}, Total value: {total_value}")
            return round(total_value, 2)
        except Exception as e:
            logging.error(f"Error fetching HSBC FTSE All-World price: {e}")
            raise

    current_total_value = 0.0

    for asset in AJ_BELL_PORTFOLIO:
        asset_quantity: float = asset["quantity"]
        logging.info(f"Processing AJ Bell asset with quantity: {asset_quantity}")
        current_total_value = _get_hsbc_ftse_all_world_price(asset_quantity)

    logging.info(f"AJ Bell total value: {current_total_value}")
    return current_total_value


def calculate_vanguard_portfolio_value():
    def _get_eod_adj_close_price(asset_ticker) -> tuple[float, str, float]:
        try:
            logging.info(f"Fetching EOD adjusted close price for {asset_ticker}.")
            http = urllib3.PoolManager()
            url = f"https://eodhd.com/api/eod/{asset_ticker}?api_token={EODHD_API_KEY}&fmt=json&order=d"
            response = http.request("GET", url)
            data = json.loads(response.data.decode("utf-8"))

            current_adj_close_price: float = data[0]["adjusted_close"]
            current_adj_close_date: str = data[0]["date"]
            prev_adj_close_price: float = data[1]["adjusted_close"]

            logging.info(
                f"Fetched prices for {asset_ticker} - Current: {current_adj_close_price}, "
                f"Previous: {prev_adj_close_price}, Date: {current_adj_close_date}"
            )
            return current_adj_close_price, current_adj_close_date, prev_adj_close_price
        except Exception as e:
            logging.error(
                f"Error fetching EOD adjusted close price for {asset_ticker}: {e}"
            )
            raise

    current_total_value = 0.0
    prev_total_value = 0.0

    for asset in VANGUARD_PORTFOLIO:
        asset_ticker: str = asset["asset_ticker"]
        asset_quantity: float = asset["quantity"]
        logging.info(
            f"Processing Vanguard asset: {asset_ticker}, Quantity: {asset_quantity}"
        )

        if asset_ticker == "cash":
            logging.info("Processing cash asset.")
            current_total_value += asset_quantity
            prev_total_value += asset_quantity
        else:
            (
                current_adj_close_price,
                current_adj_close_date,
                prev_adj_close_price,
            ) = _get_eod_adj_close_price(asset_ticker)
            total_current_asset_value: float = round(
                current_adj_close_price * asset_quantity, 2
            )
            total_prev_asset_value: float = round(
                prev_adj_close_price * asset_quantity, 2
            )

            logging.info(
                f"Asset: {asset_ticker}, Current Value: {total_current_asset_value}, "
                f"Previous Value: {total_prev_asset_value}"
            )

            prev_total_value += total_prev_asset_value
            current_total_value += total_current_asset_value

    percentage_change: float = round(
        ((current_total_value - prev_total_value) / prev_total_value) * 100, 2
    )

    logging.info(
        f"Vanguard total value: {current_total_value}, Percentage change: {percentage_change}"
    )
    return current_total_value, current_adj_close_date, percentage_change


def main():
    try:
        # Vanguard Portfolio Calculation
        logging.info("Starting Vanguard portfolio calculation.")
        vanguard_total_value, vanguard_date_time, vanguard_percentage_change = (
            calculate_vanguard_portfolio_value()
        )

        fmtd_vanguard_total_value: str = f"£{vanguard_total_value:,.2f}"
        fmtd_vanguard_date_time: str = datetime.strptime(
            vanguard_date_time, "%Y-%m-%d"
        ).strftime("%d %B %Y")
        fmtd_vanguard_percentage_change: str = (
            f"+{vanguard_percentage_change}%"
            if vanguard_percentage_change >= 0
            else f"{vanguard_percentage_change}%"
        )

        # AJ Bell Dodl Portfolio Calculation
        logging.info("Starting AJ Bell Dodl portfolio calculation.")
        fidelity_total_value = calculate_aj_bell_dodl_portfolio_value()
        fmtd_fidelity_total_value: str = f"£{fidelity_total_value:,.3f}"

        # Combine Portfolio Calculation
        combined_total_value: float = vanguard_total_value + fidelity_total_value
        fmtd_combined_total_value: str = f"£{combined_total_value:,.2f}"

        message = (
            f"\nVanguard Portfolio: **{fmtd_vanguard_total_value}**\n"
            f"Prev. Close Change: **{fmtd_vanguard_percentage_change}**\n"
            f"Last Close: **{fmtd_vanguard_date_time}**\n"
            f"\nAJ Bell Dodl Portfolio: **{fmtd_fidelity_total_value}**\n"
            f"\nTotal Combined Portfolio Value: **{fmtd_combined_total_value}**\n"
        )

        logging.info("Sending message to webhook.")
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
        logging.info(f"Message sent, response status: {response.status}")
        return response.status
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        return 500


if __name__ == "__main__":
    logging.info("Starting portfolio tracking script.")
    while True:
        now = datetime.now(pytz.timezone("Europe/London"))
        current_time = now.strftime("%H:%M")

        if current_time == "09:00":
            logging.info("Triggering portfolio calculations.")
            main()
            time.sleep(60)
        else:
            time.sleep(10)
