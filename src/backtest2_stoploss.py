import pandas as pd
import plotly.express as px
from config import DATA_PROCESSED, INITIAL_CAPITAL_CHF, STOP_LOSS, TAKE_PROFIT

def run_backtest_with_exits(returns, weights):
    portfolio_value = INITIAL_CAPITAL_CHF
    equity_curve = []
    active_weights = weights.copy()

    # Tracking of the return since the Entry (all enter on t=0)
    cumulative_from_entry = pd.Series(0.0, index = weights.index)

    for date in returns.index:
        day_returns = returns.loc[date, weights.index]

        # Daily return (sizes are not normalized; diference goes to cash with 0 return) at the BEGINING of the day
        daily_portfolio_return = (day_returns * active_weights).sum()
        portfolio_value *= (1 + daily_portfolio_return)

        # Update cummulative return from Entry (only existing assets)
        for ticker in active_weights.index: 
            if active_weights[ticker] > 0:
                cumulative_from_entry[ticker] = (1 + cumulative_from_entry[ticker]) * (1 + day_returns[ticker]) - 1
                
        # Apply Stops / Takes at CLOSE 
        for ticker in active_weights.index: 
            if active_weights[ticker] > 0:
                if cumulative_from_entry[ticker] <= STOP_LOSS or cumulative_from_entry[ticker] >= TAKE_PROFIT:
                    active_weights[ticker] = 0

        equity_curve.append({
            "date": date,
            "portfolio_return": daily_portfolio_return,
            "portfolio_value": portfolio_value
        })

    output = pd.DataFrame(equity_curve).set_index("date")

    # Insert day 0 with Initial Capital
    first_date = output.index[0] - pd.Timedelta(days = 1)
    initial_row = pd.DataFrame(
        {"portfolio_return": 0.0, "portfolio_value": INITIAL_CAPITAL_CHF},
        index = [first_date]
    )
    output = pd.concat([initial_row, output]).sort_index()

    return output

if __name__ == "__main__": 
    returns = pd.read_csv(DATA_PROCESSED / "daily_returns.csv", index_col = 0, parse_dates = True)
    weights = pd.read_csv(DATA_PROCESSED / "optimized_weights.csv", index_col = 0)["weight"]

    output = run_backtest_with_exits(returns, weights)

    output_path = DATA_PROCESSED / "backtest_results2.csv"
    output.to_csv(output_path)

    print(f"Saved backtest with exits to {output_path}")
    print(output.tail())

    fig = px.line(
        output, 
        y = "portfolio_value",
        title = "Portfolio Backtest with Stop-Loss and Take-Profit",
        labels = {"portfolio_value": "Portfolio Value", "date": "Date"}
    )

    fig.show()
