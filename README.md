# Quant Portfolio: Strategy Comparison & Backtesting

A Python backtesting framework comparing four portfolio strategies on a US equity universe over a 4.5-year period (Sep 2021 – Mar 2026). Built as a personal project to deepen practical understanding of portfolio construction, risk-adjusted performance, and the methodological pitfalls of ML in finance.

---

## TL;DR

| Strategy | Total Return | CAGR | Sharpe | Sortino | Calmar | Max Drawdown |
|---|---:|---:|---:|---:|---:|---:|
| **Static** (buy-and-hold) | 97.0% | 16.3% | 0.72 | 0.81 | 0.71 | -22.97% |
| **Stop-Loss / Take-Profit** | 79.6% | 13.9% | 0.68 | 0.74 | **0.85** | **-16.42%** |
| **ML Portfolio** (Random Forest) | 20.7% | 4.3% | 0.19 | 0.22 | 0.15 | -27.71% |
| **Monthly Rebalance** | 16.2% | 3.4% | 0.16 | 0.19 | 0.18 | -18.83% |

*Common period (2021-09-29 to 2026-03-27), all strategies rebased to CHF 5,000.*

**Key takeaway:** the simplest strategy with discipline (Stop-Loss / Take-Profit) delivered the best risk-adjusted profile. The ML strategy, when properly validated, did not beat the buy-and-hold benchmark — a result that emerged only after fixing four subtle bugs that had initially inflated its return to 134%.

---

## The Four Bugs

This project is also a documented case study of how subtle implementation errors can fabricate fictitious outperformance in financial backtests.

### Bug 1 — Compounding via addition instead of multiplication

The Stop-Loss strategy initially produced a Sharpe ratio of 27 and a 0% maximum drawdown — mathematical impossibility. Root cause:

```python
# Wrong
portfolio_value += (1 + daily_return)

# Correct
portfolio_value *= (1 + daily_return)
```

Adding `(1 + return)` ≈ adding 1 each day regardless of direction, producing a strictly increasing equity curve uncorrelated with actual portfolio behavior.

### Bug 2 — Temporal leakage in ML training set

The ML Portfolio used `target_next_1m = px.shift(-21)`, predicting one-month-forward returns. Initially, the training filter was `features[features.index < date]`, which included examples whose target was fully realized on the same day as the prediction.

Fix: enforce an embargo equal to the target horizon, decoupling the latest training label from the prediction date:

```python
EMBARGO_BDAYS = 21  # = target_next_1m horizon
train_cutoff = date - pd.tseries.offsets.BDay(EMBARGO_BDAYS)
train_data = features[features.index < train_cutoff]
```

This is the standard purged cross-validation principle (López de Prado, 2018).
**Impact:** removed roughly 80 percentage points of inflated return.

### Bug 3 — Calendar misalignment with weekends and holidays

`pandas.resample("ME").last()` produces calendar month-ends that fall on weekends (e.g., 2021-10-31 was a Sunday) or market holidays (Good Friday 2024). The loop's `current_data.empty` check silently skipped entire months when the date wasn't in the trading calendar.

Fix: derive month-end dates from the actual trading data, not from synthetic frequency rules:

```python
monthly_dates = pd.Series(returns.index).groupby(
    [returns.index.year, returns.index.month]
).max().values
monthly_dates = pd.DatetimeIndex(monthly_dates).sort_values()
```

### Bug 4 — Edge effect at the end of the backtest

The ML feature pipeline ends earlier than the price data because lagging windows (`shift(-21)`) consume tail observations. Forward-fill in the comparison script made it look like the ML portfolio kept its value during the missing month, artificially deflating volatility and biasing risk metrics.

Fix: truncate the common period to the last date with real data across all strategies (`COMMON_END = "2026-03-27"`).

---

## Strategies Implemented

| Strategy | Logic |
|---|---|
| **Static** | Buy-and-hold with one-time mean-variance optimization (max Sharpe, weight cap 20%). |
| **Stop-Loss / Take-Profit** | Static weights, but each asset exits permanently if cumulative return from entry breaches `-20%` (stop) or `+100%` (take). Capital reallocates to surviving assets via renormalization. |
| **Monthly Rebalance** | Re-runs the mean-variance optimizer every month using the trailing 252 days of returns. Stop-loss / take-profit applied within each holding period. |
| **ML Portfolio** | Random Forest regressor predicts 1-month-forward returns at each month-end. Top 5 predicted assets are passed to the mean-variance optimizer. Re-trained monthly with a 21-business-day embargo against temporal leakage. |

---

## Methodology Notes

**Two analyses are provided:**

1. **Full Operational Period** — each strategy is evaluated over its complete deployable history. Reflects realistic operating performance, but Total Return values are not directly comparable across strategies because each operated over a different time window (the ML strategy requires 200+ days of training data and starts later than Static).

2. **Common Period (Head-to-Head)** — all strategies are truncated to the period when every strategy was simultaneously active and rebased to the same initial capital. This enables apples-to-apples comparison.

The TL;DR table above uses the Common Period analysis.

**Sharpe ratio** uses the standard convention: annualized arithmetic return minus risk-free rate, divided by annualized volatility. `RISK_FREE_RATE_CHF = 0.01` (constant).

---

## Limitations

- **Universe size**: 5 US equities (AAPL, ABBV, ACGL, ADI, ADM). A wider universe would change all results.
- **No transaction costs**: not modeled. At monthly rebalancing frequency the impact is small (~0.2% annually for retail brokerage), but for a daily strategy this would dominate.
- **Constant risk-free rate**: `RISK_FREE_RATE_CHF = 0.01`. The actual SARON varied between -0.75% and 1.75% during the backtest period.
- **No hyperparameter tuning**: ML model uses default parameters (`n_estimators=200, max_depth=6`). Proper tuning would require a separate validation set with purged cross-validation.
- **One-shot exits in Stop-Loss strategy**: assets that hit thresholds remain in cash with zero return until the end of the backtest. Re-entry on rebalancing is not modeled.

---

## Project Structure
```
quant_portfolio_jsbr/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/              # IBKR-downloaded prices
│   └── processed/        # daily returns, features, equity curves, metrics
└── src/
├── config.py
├── universe.py
├── ibkr_loader.py
├── features.py
├── optimizer.py
│
├── backtest_static.py
├── backtest_stoploss.py
├── backtest_rebalance.py
├── backtest_ml.py
│
├── compare_all_ml.py            # combines individual equity curves
├── compare_all_common_period.py  # truncates to common period + rebases
│
├── performance_compare.py        # metrics for full operational period
├── performance_compare_cp.py     # metrics for common period
│
├── strategy_ranking.py           # ranking on full operational period
└── strategy_ranking_cp.py        # ranking on common period
```
---

## How to Reproduce

### 1. Setup

```bash
git clone https://github.com/SaulBars19/quant-portfolio-jsbr.git
cd quant-portfolio-jsbr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get the price data

This project uses Interactive Brokers historical data via the `ibapi` library. To reproduce with your own IBKR connection, configure credentials in `config.py` and run:

```bash
python src/ibkr_loader.py
```

The download script writes to `data/raw/ibkr_prices.csv`.

### 3. Run the pipeline

```bash
# 1. Compute daily returns and ML features
python src/features.py

# 2. Optimize portfolio weights
python src/optimizer.py

# 3. Run the four backtests
python src/backtest_static.py
python src/backtest_stoploss.py
python src/backtest_rebalance.py
python src/backtest_ml.py

# 4. Combine and compare
python src/compare_all_ml.py
python src/compare_all_common_period.py

# 5. Compute performance metrics
python src/performance_compare.py
python src/performance_compare_cp.py

# 6. Final ranking
python src/strategy_ranking.py
python src/strategy_ranking_cp.py
```

---

## Roadmap

- [ ] Modeling of transaction costs and slippage
- [ ] Walk-forward cross-validation with purged folds for hyperparameter tuning
- [ ] Expanded universe (full S&P 500 / Nasdaq 100 / SMI)
- [ ] Multi-currency portfolio with FX hedging
- [ ] Daily rebalancing variant with appropriate target horizon
- [ ] Risk parity and Black-Litterman as additional strategies

---

## References

- López de Prado, Marcos. *Advances in Financial Machine Learning*. Wiley, 2018. (Chapter 7 on purged cross-validation and embargo.)
- Markowitz, Harry. "Portfolio Selection." *The Journal of Finance*, 1952.
- Sharpe, William F. "The Sharpe Ratio." *Journal of Portfolio Management*, 1994.

---

## Author

**José Saúl Barrientos Rivera** — M.A. Economics & Management (Applied Data Science), University of Lucerne.
[LinkedIn](https://www.linkedin.com/in/saul-barrientos/) | [GitHub](https://github.com/SaulBars19)

CFA Level I candidate (2027).

