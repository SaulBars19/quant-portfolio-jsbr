import pandas as pd
import numpy as np
from scipy.optimize import minimize
from config import DATA_PROCESSED, RISK_FREE_RATE_CHF, MAX_WEIGHT

def portfolio_performance(weights, mean_returns, cov_matrix):
    portfolio_return = np.dot(weights, mean_returns)
    portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)

    sharpe = (portfolio_return - RISK_FREE_RATE_CHF) / portfolio_volatility

    return portfolio_return, portfolio_volatility, sharpe

def negative_sharpe(weights, mean_returns, cov_matrix):
    return -portfolio_performance(weights, mean_returns, cov_matrix)[2]

def optimize_portfolio(returns):
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    n_assets = len(returns.columns)

    initial_weights = np.array([1 / n_assets] * n_assets)

    bounds = tuple((0, MAX_WEIGHT) for _ in range(n_assets))

    constraints = {
        "type": "eq",
        "fun": lambda weights: np.sum(weights) - 1
    }

    result = minimize(
        negative_sharpe,
        initial_weights,
        args = (mean_returns, cov_matrix),
        method = "SLSQP",
        bounds = bounds, 
        constraints = constraints
    )

    weights = pd.Series(result.x, index = returns.columns)
    weights = weights[weights > 0.001]
    weights = weights / weights.sum()

    return weights

if __name__ == "__main__":
    returns = pd.read_csv(DATA_PROCESSED / "daily_returns.csv", index_col = 0, parse_dates = True)

    weights = optimize_portfolio(returns)

    output_path = DATA_PROCESSED / "optimized_weights.csv"
    weights.to_csv(output_path, header = ["weight"])

    print("Optimized portfolio weights:")
    print(weights.sort_values(ascending = False))

    print(f"Saved weights to {output_path}")