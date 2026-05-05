import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from config import DATA_PROCESSED, INITIAL_CAPITAL_CHF
from optimizer import optimize_portfolio

def run_ml_portfolio(prices, features): 
    returns = prices.pct_change().dropna()

    portfolio_value = INITIAL_CAPITAL_CHF
    equity_curve = []

    monthly_dates = pd.Series(returns.index).groupby(
        [returns.index.year, returns.index.month]
    ).max().values
    monthly_dates = pd.DatetimeIndex(monthly_dates)


    model = RandomForestRegressor(
        n_estimators = 200,
        max_depth = 6,
        random_state = 42
    )

    for i, date in enumerate(monthly_dates[:-1]):
        # Only uses training data which target is totally done before of 'date'
        EMBARGO_BDAYS = 21 # = exact target horizon in business days
        train_cutoff = date - pd.tseries.offsets.BDay(EMBARGO_BDAYS)
        train_data = features[features.index < train_cutoff]

        if len(train_data) < 200:
            continue

        feature_cols = ["ret_1m", "ret_3m", "vol_1m", "vol_3m", "drawdown"]

        X_train = train_data[feature_cols]
        y_train = train_data["target_next_1m"]

        model.fit(X_train, y_train)

        current_data = features[features.index == date]

        if current_data.empty: 
            continue

        X_current = current_data[feature_cols]

        current_data = current_data.copy()
        current_data["predicted"] = model.predict(X_current)

        top_assets = current_data.sort_values("predicted", ascending = False).head(5)["ticker"]

        hist_returns = returns[top_assets].loc[:date].tail(252)

        weights = optimize_portfolio(hist_returns)

        next_date = monthly_dates[i + 1]
        period_returns = returns.loc[date:next_date, weights.index]

        for d in period_returns.index:
            daily_ret = period_returns.loc[d] @ weights
            portfolio_value *= (1 + daily_ret)

            equity_curve.append({
                "date": d,
                "portfolio_return": daily_ret,
                "portfolio_value": portfolio_value
            })

    output = pd.DataFrame(equity_curve).drop_duplicates("date", keep = "last").set_index("date")

    # Insert day 0 with Initial Capital
    first_date = output.index[0] - pd.Timedelta(days = 1)
    inital_row = pd.DataFrame(
        {"portfolio_return": 0.0, "portfolio_value": INITIAL_CAPITAL_CHF},
        index = [first_date]
    )
    output = pd.concat([inital_row,output]).sort_index()

    return output

if __name__ == "__main__": 
    prices = pd.read_csv(
        DATA_PROCESSED.parent / "raw" / "ibkr_prices.csv",
        index_col = 0,
        parse_dates = True
    )

    features = pd.read_csv(
        DATA_PROCESSED / "ml_features.csv",
        index_col = 0,
        parse_dates = True
    )

    equity = run_ml_portfolio(prices,features)

    output_path = DATA_PROCESSED / "ml_portfolio.csv"
    equity.to_csv(output_path)
    
    print(f"Saved ML portfolio to {output_path}")
    print(equity.tail())

    fig = px.line(
        equity,
        y = "portfolio_value",
        title = "ML Portfolio Backtest",
        labels = {"portfolio_value": "Portfolio Value"}
    )

    fig.show()