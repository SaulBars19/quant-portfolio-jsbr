import pandas as pd
import plotly.express as px
from config import DATA_PROCESSED, INITIAL_CAPITAL_CHF

def run_backtest(returns, weights):
    portfolio_returns = returns[weights.index] @ weights 
    equity_curve = (1 + portfolio_returns).cumprod() * INITIAL_CAPITAL_CHF

    # Insert day 0 with Initial Capital before Returns are applied
    first_date = equity_curve.index[0] - pd.Timedelta(days = 1)
    equity_curve = pd.concat([
        pd.Series({first_date: INITIAL_CAPITAL_CHF}),
        equity_curve
    ]).sort_index()

    portfolio_returns = pd.concat([
        pd.Series({first_date: 0.0}),
        portfolio_returns
    ]).sort_index()
    
    return portfolio_returns, equity_curve

if __name__ == "__main__":
    returns = pd.read_csv(DATA_PROCESSED / "daily_returns.csv", index_col = 0, parse_dates = True)
    weights = pd.read_csv(DATA_PROCESSED / "optimized_weights.csv", index_col = 0) ["weight"]

    portfolio_returns, equity_curve = run_backtest(returns, weights)

    output = pd.DataFrame({
        "portfolio_return": portfolio_returns,
        "portfolio_value": equity_curve
    })

    output_path = DATA_PROCESSED / "backtest_results.csv"
    output.to_csv(output_path)

    print(f"Saved backtest results to {output_path}")
    print(output.tail())

    fig = px.line(
        output,
        y = "portfolio_value",
        title = "Portfolio Backtest Value",
        labels = {"portfolio_value": "Portfolio Value", "index": "Date"}
    )

    fig.show()