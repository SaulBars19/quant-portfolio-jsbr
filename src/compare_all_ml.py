import pandas as pd
import plotly.express as px
from config import DATA_PROCESSED

def load_strategy(filename, column_name, strategy_name):
    df = pd.read_csv(
        DATA_PROCESSED / filename,
        index_col = 0, 
        parse_dates = True
    )

    # Delete duplicate Dates
    df = df[~df.index.duplicated(keep = "last")]

    # Order by date
    df = df.sort_index()

    # Take only portfolio_value and rename
    series = df[column_name].rename(strategy_name)

    return series

if __name__ == "__main__":
    static = load_strategy(
        "backtest_results.csv",
        "portfolio_value",
        "Static"
    )

    stop_loss = load_strategy(
        "backtest_results2.csv",
        "portfolio_value",
        "Stop-Loss / Take-Profit"
    )

    rebalance = load_strategy(
        "rebalance_backtest.csv",
        "portfolio_value",
        "Monthly Rebalance"
    )

    ml = load_strategy(
        "ml_portfolio.csv",
        "portfolio_value",
        "ML Portfolio"
    )

    # Create common Index from minimum date to max date
    all_series = [static, stop_loss, rebalance, ml]

    start_date = min(s.index.min() for s in all_series)
    end_date = max(s.index.max() for s in all_series)

    common_index = pd.date_range(
        start = start_date,
        end = end_date,
        freq = "D"
    )

    # Reindex and forward fill
    df = pd.concat(all_series, axis = 1)
    df = df.reindex(common_index)
    df = df.ffill()

    # Delete files where no data is available
    df = df.dropna (how = "all")

    output_path = DATA_PROCESSED / "strategy_comparison_full.csv"
    df.to_csv(output_path)

    print(f"Saved strategy comparison to {output_path}")
    print("\nDuplicated dates after cleaning:")
    print(df.index.duplicated().sum())

    print("\nDate range:")
    print(df.index.min(), "to", df.index.max())

    print("\nFinal Values:")
    print(df.tail(1))


    fig = px.line(
        df,
        title = "Strategy Comparison: Static vs Stop-Loss vs Rebalance vs ML",
        labels = {"value": "Portfolio Value", "index": "Date", "variable": "Strategy"}
    )

    fig.show()
