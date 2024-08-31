import json
from datetime import datetime
import urllib3
from lxml import html
import re
from config import VANGUARD_PORTFOLIO, AJ_BELL_PORTFOLIO, EODHD_API_KEY, WEBHOOK_URL


def get_eod_adj_close_price(asset_ticker) -> tuple[float, str, float]:
    http = urllib3.PoolManager()
    url = f"https://eodhd.com/api/eod/{asset_ticker}?api_token={EODHD_API_KEY}&fmt=json&order=d"
    response = http.request("GET", url)
    data = json.loads(response.data.decode("utf-8"))

    current_adj_close_price: float = data[0]["adjusted_close"]
    current_adj_close_date: str = data[0]["date"]

    prev_adj_close_price: float = data[1]["adjusted_close"]

    return current_adj_close_price, current_adj_close_date, prev_adj_close_price


def calculate_vanguard_portfolio_value():
    current_total_value = 0.0
    prev_total_value = 0.0

    for asset in VANGUARD_PORTFOLIO:
        asset_ticker: str = asset["asset_ticker"]
        asset_quantity: float = asset["quantity"]

        if asset_ticker == "cash":
            current_total_value += asset_quantity
            prev_total_value += asset_quantity
        else:
            current_adj_close_price, current_adj_close_date, prev_adj_close_price = (
                get_eod_adj_close_price(asset_ticker)
            )
            total_current_asset_value: float = round(
                current_adj_close_price * asset_quantity, 2
            )
            total_prev_asset_value: float = round(
                prev_adj_close_price * asset_quantity, 2
            )

            prev_total_value += total_prev_asset_value
            current_total_value += total_current_asset_value

    percentage_change: float = round(
        ((current_total_value - prev_total_value) / prev_total_value) * 100, 2
    )

    return current_total_value, current_adj_close_date, percentage_change


def calculate_fidelity_portfolio_value():
    def get_hsbc_ftse_all_world_price(quantity: float) -> float:
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

        total_value = round((quantity * price), 2)
        return total_value

    current_total_value = 0.0

    for asset in AJ_BELL_PORTFOLIO:
        asset_quantity: float = asset["quantity"]
        current_total_value = get_hsbc_ftse_all_world_price(asset_quantity)

    return current_total_value


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
    except Exception:
        return 500


def lambda_handler(event, context):
    # Vanguard Portfolio Calculation
    vanguard_total_value, vanguard_date_time, vanguard_percentage_change = calculate_vanguard_portfolio_value()

    fmtd_vanguard_total_value: str = f"£{vanguard_total_value:,.2f}"
    fmtd_vanguard_date_time: str = datetime.strptime(vanguard_date_time, "%Y-%m-%d").strftime("%d %B %Y")
    fmtd_vanguard_percentage_change: str = (
        f"+{vanguard_percentage_change}%" if vanguard_percentage_change >= 0 else f"{vanguard_percentage_change}%"
    )

    # Fidelity Portfolio Calculation
    fidelity_total_value = calculate_fidelity_portfolio_value()
    fmtd_fidelity_total_value: str = f"£{fidelity_total_value:,.2f}"

    # Total combined value of both portfolios
    combined_total_value: float = vanguard_total_value + fidelity_total_value
    fmtd_combined_total_value: str = f"£{combined_total_value:,.2f}"

    # Construct message
    message = (
        f"\nVanguard Portfolio: **{fmtd_vanguard_total_value}**\n"
        f"Prev. Close Change: **{fmtd_vanguard_percentage_change}**\n"
        f"Last Close: **{fmtd_vanguard_date_time}**\n"
        f"\nFidelity Portfolio: **{fmtd_fidelity_total_value}**\n"
        f"\nTotal Combined Portfolio Value: **{fmtd_combined_total_value}**\n"
    )

    # Sending the webhook message
    send_webhook_message(message)

lambda_handler(event=None, context=None)

