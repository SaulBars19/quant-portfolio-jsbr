import pandas as pd
from config import DATA_RAW, DATA_PROCESSED

def calculate_daily_returns(prices):
    returns = prices.pct_change()
    returns = returns.dropna(how = "all")
    return returns

if __name__ == "__main__":
    prices = pd.read_csv(DATA_RAW / "ibkr_prices.csv", index_col = 0, parse_dates = True)

    returns = calculate_daily_returns(prices)

    output_path = DATA_PROCESSED / "daily_returns.csv"
    returns.to_csv(output_path)

    print(f"Saved daily returns to {output_path}")
    print(returns.tail())