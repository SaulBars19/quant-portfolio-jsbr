import pandas as pd
import numpy as np
from config import DATA_PROCESSED, RISK_FREE_RATE_CHF

def calculate_metrics(series, periods_per_year = 252, risk_free = RISK_FREE_RATE_CHF):
    series = series.dropna()
    if len(series) < 2: 
        return None

    returns = series.pct_change().dropna()

    # Return metrics
    total_return = series.iloc[-1] / series.iloc[0] -1
    years = (series.index[-1] - series.index[0]).days / 365.25
    cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else np.nan

    # Annualized arithmetic return for Sharpe (Standard convention)
    ann_return = returns.mean() * periods_per_year

    # Risk metrics
    volatility = returns.std() * np.sqrt(periods_per_year)
    downside = returns[returns < 0]
    downside_vol = downside.std() * np.sqrt(periods_per_year)

    drawdown = series / series.cummax() -1
    max_drawdown = drawdown.min()

    # Risk-adjusted ratios (with guards against division by zero)
    sharpe = (ann_return - risk_free) / volatility if volatility > 0 else np.nan
    sortino = (ann_return - risk_free) / downside_vol if downside_vol > 0 else np.nan
    calmar = cagr / abs(max_drawdown) if max_drawdown < 0 else np.nan

    return{
        "Initial Value": series.iloc[0],
        "Final Value": series.iloc [-1],
        "Total Return": total_return,
        "CAGR": cagr,
        "Annual Volatility": volatility,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Calmar Ratio": calmar,
        "Max Drawdown": max_drawdown,
    }

if __name__ == "__main__":
    df = pd.read_csv(
        DATA_PROCESSED / "strategy_comparison_full.csv",
        index_col = 0, 
        parse_dates = True
    )

    results = {}

    for strategy in df.columns: 
        results[strategy] = calculate_metrics(df[strategy])

    metrics_df = pd.DataFrame(results).T

    output_path = DATA_PROCESSED / "performance_comparison.csv"
    metrics_df.to_csv(output_path)

    print("\nPerformance Comparison:")
    print(metrics_df)

    print(f"\nSaved performance comparison to {output_path}")