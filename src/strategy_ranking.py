import pandas as pd
from config import DATA_PROCESSED

def rank_strategies(metrics_df):
    ranking = metrics_df.copy()

    ranking["Sharpe Rank"] = ranking["Sharpe Ratio"].rank(ascending=True)
    ranking["CAGR Rank"] = ranking["CAGR"].rank(ascending=True)
    ranking["Calmar Rank"] = ranking["Calmar Ratio"].rank(ascending=True)
    ranking["Sortino Rank"] = ranking["Sortino Ratio"].rank(ascending=True)
    ranking["Drawdown Rank"] = ranking["Max Drawdown"].rank(ascending=False)
    ranking["Volatility Rank"] = ranking["Annual Volatility"].rank(ascending=False)

    ranking["Final Score"] = (
        ranking["Sharpe Rank"] * 0.30 +
        ranking["CAGR Rank"] * 0.20 +
        ranking["Calmar Rank"] * 0.15 + 
        ranking["Sortino Rank"] * 0.15 + 
        ranking["Drawdown Rank"] * 0.10 +
        ranking["Volatility Rank"] * 0.10
    )

    ranking = ranking.sort_values("Final Score", ascending=False)

    return ranking

if __name__ == "__main__":
    metrics = pd.read_csv(
        DATA_PROCESSED / "performance_comparison.csv",
        index_col = 0
    )

    ranking = rank_strategies(metrics)

    output_path = DATA_PROCESSED / "strategy_ranking.csv"
    ranking.to_csv(output_path)

    print("\nStrategy Ranking")
    print(ranking)

    print(f"\nSaved strategy ranking to {output_path}")