import pandas as pd
import plotly.express as px
from performance_compare import calculate_metrics
from config import DATA_PROCESSED, INITIAL_CAPITAL_CHF


# Coomon period from whre all the strategies are active
COMMON_START = "2021-09-29"
COMMON_END = "2026-03-27"

if __name__ == "__main__":
    # 1. Load combined CSV
    df = pd.read_csv(
        DATA_PROCESSED / "strategy_comparison_full.csv",
        index_col = 0,
        parse_dates = True
    )

    # 2. Truncate to common period
    df = df.loc[COMMON_START:COMMON_END]

    # 3. Rebase: all strategies start at INITIAL_CAPITAL_CHF
    df = df / df.iloc[0] * INITIAL_CAPITAL_CHF

    # 4. Save rebased equity curves
    output_path = DATA_PROCESSED / "strategy_comparison_same_period.csv"
    df.to_csv(output_path)

    print(f"Saved comparable equity curves to {output_path}")
    print(f"Period: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Years covered: {(df.index[-1] - df.index[0]).days / 365.25:.2f}")

    print("\nFirst values (all should be 5,000.00):")
    print(df.head(1).round(2))

    print("\nFinal values:")
    print(df.tail(1).round(2))

    # 5. Compute metrics 

    results = {strategy: calculate_metrics(df[strategy]) for strategy in df.columns}
    metrics_df = pd.DataFrame(results).T

    metrics_path = DATA_PROCESSED / "performance_comparison_same_period.csv"
    metrics_df.to_csv(metrics_path)

    print("\n" + "=" * 80)
    print("Performance Comparison - Common Period (Head-to-Head)")
    print("=" * 80)
    print(metrics_df.to_string(formatters= {
        "Initial Value": "{:>10,.2f}".format,
        "Final Value": "{:>10,.2f}".format,
        "Total Return": "{:>8.2%}".format,
        "CAGR": "{:>8.2%}".format,
        "Annual Volatility": "{:>8.2%}".format,
        "Sharpe Ratio": "{:>7.3f}".format,
        "Sortino Ratio": "{:>7.3f}".format,
        "Calmar Ratio": "{:>7.3f}".format,
        "Max Drawdown": "{:>8.2%}".format,
    }))

    print(f"\nSaved performance metrics to {metrics_path}")

    # 6. Plot
    fig = px.line(
        df,
        title = f"Strategy Comparison - Common Period ({df.index[0].date()} to {df.index[-1].date()})",
        labels = {
            "value": "Portfolio Value (CHF)",
            "index": "Date",
            "variable": "Strategy"
        }
    )
    fig.update_layout(
        legend_title_text = "Strategy",
        hovermode = "x unified"
    )
    fig.show()
