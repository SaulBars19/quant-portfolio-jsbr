from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

import threading 
import time
from pathlib import Path

import pandas as pd

class IBKRHistoricalDataApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)

        self.data = {}
        self.finished_requests = set()
        self.current_symbol_by_req_id = {}

    def historicalData(self, reqId, bar):
        symbol = self.current_symbol_by_req_id[reqId]

        if symbol not in self.data: 
            self.data[symbol] = []

        self.data[symbol].append(
            {
                "Date": bar.date,
                "Open": bar.open,
                "High": bar.high,
                "Low": bar.low,
                "Close": bar.close,
                "Volume": bar.volume,
            }
        )

    def historicalDataEnd(self, reqId, start, end,):
        symbol = self.current_symbol_by_req_id[reqId]
        print(f"Finished: {symbol}")
        self.finished_requests.add(reqId)

    def error(self, reqId, errorCode, errorString, advanceOrderRejectJson = ""):
        print(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

def run_loop(app):
    app.run()

def make_stock_contract(symbol, exchange = "SMART", currency = "USD", primary_exchange = None):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency

    if primary_exchange is not None: 
        contract.primaryExchange = primary_exchange

    return contract

def download_ibkr_historical_prices(
    symbols,
    host = "127.0.0.1", 
    port = 7497,
    client_id = 1,
    duration = "5 Y",
    bar_size = "1 day",
    what_to_show = "TRADES", 
    sleep_between_requests = 2,
    max_wait_seconds = 30,
):
    app = IBKRHistoricalDataApp()

    app.connect(host, port, clientId = client_id)

    thread = threading.Thread(target = run_loop, args = (app,), daemon = True)
    thread.start()

    time.sleep(2)

    for req_id, symbol in enumerate(symbols, start = 1):
        print(f"Requesting {symbol}...")

        contract = make_stock_contract(
            symbol = symbol,
            exchange = "SMART",
            currency = "USD",
            primary_exchange = "Nasdaq" if symbol in ["AAPL", "MSFT", "GOOG", "GOOGL", "NVDA", "AMZN", "META", "TSLA"] else None,
        )

        app.current_symbol_by_req_id[req_id] = symbol

        app.reqHistoricalData(
            reqId = req_id,
            contract = contract,
            endDateTime = "",
            durationStr = duration,
            barSizeSetting = bar_size,
            whatToShow = what_to_show,
            useRTH = 1,
            formatDate = 1,
            keepUpToDate = False,
            chartOptions = [],
        )

        waited = 0

        while req_id not in app.finished_requests and waited < max_wait_seconds:
            time.sleep(1)
            waited += 1 

        if req_id not in app.finished_requests:
            print(f"Timeout: {symbol}")

        time.sleep(sleep_between_requests)

    app.disconnect()

    prices = {}

    for symbol, rows in app.data.items():
        df = pd.DataFrame(rows)

        if df.empty:
            continue

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        df = df.sort_index()

        prices[symbol] = df["Close"]

    prices_df = pd.DataFrame(prices)
    prices_df = prices_df.dropna(axis = 0, how = "all")
    prices_df = prices_df.dropna(axis = 1, how = "all")

    return prices_df

if __name__ == "__main__":
    # Initial safe demo: only data, no orders. 
    from universe import build_universe
    test_symbols = build_universe() [:10]

    prices = download_ibkr_historical_prices(
        symbols = test_symbols,
        port = 7497,
        client_id = 1,
        duration = "5 Y",
        bar_size = "1 day",
        sleep_between_requests = 2,
    )

    print(prices.head())
    print(prices.tail())
    print(f"Shape: {prices.shape}")

    output_path = Path("data/raw/ibkr_prices.csv")
    output_path.parent.mkdir(parents = True, exist_ok = True)

    prices.to_csv(output_path)
    print(f"Saved prices to {output_path}")