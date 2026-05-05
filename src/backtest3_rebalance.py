import pandas as pd
import numpy as np
import plotly.express as px
from config import DATA_PROCESSED, INITIAL_CAPITAL_CHF, STOP_LOSS, TAKE_PROFIT
from optimizer import optimize_portfolio

def run_rebalance_backtest(returns):
    portfolio_value = INITIAL_CAPITAL_CHF
    equity_curve = []

    dates = returns.index

    # Last available trading day of each month (handles weekends AND holidays)
    monthly_dates = pd.Series(returns.index).groupby(
        [returns.index.year, returns.index.month]
    ).max().values
    monthly_dates = pd.DatetimeIndex(monthly_dates)

    weights = None
    cumulative_asset_returns = None

    for i, date in enumerate(dates):
        # Monthly rebalance 
        if date in monthly_dates or weights is None : 
            hist_returns = returns.loc[:date].tail(252)

            if len(hist_returns) < 50: 
                continue 

            weights = optimize_portfolio(hist_returns)
            cumulative_asset_returns = pd.Series(0, index = weights.index)

        day_returns = returns.loc[date, weights.index]

        # Update cumulative returns per asset
        cumulative_asset_returns = (1 + cumulative_asset_returns) * (1 + day_returns) - 1

        # Stop-Loss / Take-Profit
        for ticker in weights.index: 
            if weights[ticker] == 0: 
                continue

            if cumulative_asset_returns[ticker] <= STOP_LOSS:
                weights[ticker] = 0

            elif cumulative_asset_returns[ticker] >= TAKE_PROFIT:
                weights[ticker] = 0

        if weights.sum() > 0:
            weights = weights / weights.sum()

        daily_portfolio_return = day_returns @ weights
        portfolio_value *= (1 + daily_portfolio_return)

        equity_curve.append({
            "date": date,
            "portfolio_return": daily_portfolio_return,
            "portfolio_value": portfolio_value
        })
    
    output = pd.DataFrame(equity_curve).drop_duplicates("date").set_index("date")

    # Insert day 0 with Initial Capital
    first_date = output.index[0] - pd.Timedelta(days = 1)
    initial_row = pd.DataFrame(
        {"portfolio_return": 0.0, "portfolio_value": INITIAL_CAPITAL_CHF},
        index = [first_date]
    )
    output = pd.concat([initial_row, output]).sort_index()

    return output

if __name__ == "__main__":
    returns = pd.read_csv(
        DATA_PROCESSED / "daily_returns.csv",
        index_col = 0,
        parse_dates = True
    )

    equity = run_rebalance_backtest(returns)

    output_path = DATA_PROCESSED / "rebalance_backtest.csv"
    equity.to_csv(output_path)

    print(f"Saved rebalance backtest to {output_path}")
    print(equity.tail())

    fig = px.line(
        equity,
        y = "portfolio_value",
        title = "Rebalanced Portfolio Backtest",
        labels = {"portfolio_value": "Portfolio Value"}
    )

    fig.show()